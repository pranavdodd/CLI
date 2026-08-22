import httpx
import pytest

from student_agent.integrations.canvas import CanvasClient


@pytest.mark.asyncio
async def test_canvas_normalizes_courses_and_assignments():
    def handler(request: httpx.Request):
        if request.url.path.endswith("/courses"):
            return httpx.Response(200, json=[{"id": 1, "name": "Operating Systems", "course_code": "CS 439"}])
        return httpx.Response(200, json=[{"id": 2, "name": "Project 2", "due_at": "2026-08-23T23:59:00Z", "points_possible": 100, "submission_types": ["online_upload"]}])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        canvas = CanvasClient("https://canvas.example", "token", http_client=client)
        courses = await canvas.get_courses()
        assignments = await canvas.get_assignments("1")
    assert courses[0].course_code == "CS 439"
    assert assignments[0].course_id == "1"
    assert assignments[0].points_possible == 100
