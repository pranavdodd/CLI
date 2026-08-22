from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Assignment(BaseModel):
    id: str
    course_id: str
    name: str
    description: Optional[str] = None
    due_at: Optional[datetime] = None
    points_possible: Optional[float] = None
    html_url: Optional[str] = None
    submission_types: List[str] = Field(default_factory=list)
