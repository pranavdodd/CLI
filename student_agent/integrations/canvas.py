from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from student_agent.models import Assignment, Course


class CanvasAPIError(RuntimeError):
    """Canvas returned an unusable response."""


class CanvasAuthenticationError(CanvasAPIError):
    """Canvas rejected the configured token."""


class CanvasClient:
    def __init__(self, base_url: str, access_token: str, timeout: float = 30.0, http_client: httpx.AsyncClient | None = None):
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self.timeout = timeout
        self._http_client = http_client

    async def __aenter__(self) -> CanvasClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._http_client is not None and not self._http_client.is_closed:
            await self._http_client.aclose()

    async def get_courses(self) -> list[Course]:
        data = await self._get_all("/api/v1/courses", {"enrollment_state": "active", "per_page": 100})
        return [Course(id=str(item["id"]), name=item.get("name") or item.get("course_code") or str(item["id"]), course_code=item.get("course_code"), start_at=_parse_datetime(item.get("start_at")), end_at=_parse_datetime(item.get("end_at"))) for item in data]

    async def get_assignments(self, course_id: str) -> list[Assignment]:
        data = await self._get_all(f"/api/v1/courses/{course_id}/assignments", {"per_page": 100})
        return [_assignment(item, course_id) for item in data]

    async def get_assignment(self, course_id: str, assignment_id: str) -> Assignment:
        item = await self._get(f"/api/v1/courses/{course_id}/assignments/{assignment_id}")
        return _assignment(item, course_id)

    async def get_modules(self, course_id: str) -> list[dict[str, Any]]:
        return await self._get_all(f"/api/v1/courses/{course_id}/modules", {"include[]": "items", "per_page": 100})

    async def get_files(self, course_id: str) -> list[dict[str, Any]]:
        return await self._get_all(f"/api/v1/courses/{course_id}/files", {"per_page": 100})

    async def get_upcoming_assignments(self, days: int) -> list[Assignment]:
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=days)
        assignments: list[Assignment] = []
        for course in await self.get_courses():
            for assignment in await self.get_assignments(course.id):
                if assignment.due_at and now <= assignment.due_at.astimezone(timezone.utc) <= end:
                    assignments.append(assignment)
        return sorted(assignments, key=lambda item: item.due_at or datetime.max.replace(tzinfo=timezone.utc))

    async def _get_all(self, path: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        next_url: str | None = self._url(path)
        next_params = params
        while next_url:
            response = await self._request(next_url, next_params)
            payload = response.json()
            if not isinstance(payload, list):
                raise CanvasAPIError("Canvas returned an unexpected response shape.")
            items.extend(payload)
            next_url = _next_link(response.headers.get("Link"))
            next_params = None
        return items

    async def _get(self, path: str) -> dict[str, Any]:
        response = await self._request(self._url(path), None)
        payload = response.json()
        if not isinstance(payload, dict):
            raise CanvasAPIError("Canvas returned an unexpected response shape.")
        return payload

    async def _request(self, url: str, params: dict[str, Any] | None) -> httpx.Response:
        client = self._http_client or httpx.AsyncClient(timeout=self.timeout)
        should_close = self._http_client is None
        try:
            for attempt in range(3):
                try:
                    response = await client.get(url, params=params, headers={"Authorization": f"Bearer {self.access_token}"})
                    if response.status_code in (401, 403):
                        raise CanvasAuthenticationError("Canvas authentication failed. Check your access token.")
                    if response.status_code >= 500 and attempt < 2:
                        continue
                    response.raise_for_status()
                    return response
                except httpx.TimeoutException as exc:
                    if attempt == 2:
                        raise CanvasAPIError("Canvas request timed out.") from exc
                except httpx.RequestError as exc:
                    if attempt == 2:
                        raise CanvasAPIError(f"Canvas request failed: {exc}") from exc
            raise CanvasAPIError("Canvas request failed after retries.")
        finally:
            if should_close:
                await client.aclose()

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"


def _assignment(item: dict[str, Any], course_id: str) -> Assignment:
    return Assignment(id=str(item["id"]), course_id=course_id, name=item.get("name", "Untitled assignment"), description=item.get("description"), due_at=_parse_datetime(item.get("due_at")), points_possible=item.get("points_possible"), html_url=item.get("html_url"), submission_types=item.get("submission_types") or [])


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _next_link(header: str | None) -> str | None:
    if not header:
        return None
    for part in header.split(","):
        url, _, rel = part.strip().partition(";")
        if 'rel="next"' in rel:
            return url.strip("<>")
    return None
