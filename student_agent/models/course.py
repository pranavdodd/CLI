from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Course(BaseModel):
    id: str
    name: str
    course_code: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
