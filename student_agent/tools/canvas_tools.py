from pydantic import BaseModel, Field

from student_agent.integrations.canvas import CanvasClient
from student_agent.tools.base import make_tool


class CourseAssignmentsArgs(BaseModel):
    course_id: str = Field(min_length=1)


class AssignmentArgs(BaseModel):
    course_id: str = Field(min_length=1)
    assignment_id: str = Field(min_length=1)


class UpcomingArgs(BaseModel):
    days: int = Field(default=7, ge=1, le=90)


class CourseArgs(BaseModel):
    course_id: str = Field(min_length=1)


def canvas_tools(client: CanvasClient):
    async def courses():
        return [item.model_dump(mode="json") for item in await client.get_courses()]

    async def assignments(course_id: str):
        return [item.model_dump(mode="json") for item in await client.get_assignments(course_id)]

    async def upcoming(days: int = 7):
        return [item.model_dump(mode="json") for item in await client.get_upcoming_assignments(days)]

    async def assignment(course_id: str, assignment_id: str):
        return (await client.get_assignment(course_id, assignment_id)).model_dump(mode="json")

    async def modules(course_id: str):
        return await client.get_modules(course_id)

    async def files(course_id: str):
        return await client.get_files(course_id)

    return [
        make_tool("canvas_get_courses", "Retrieve the student's active Canvas courses.", BaseModel, courses),
        make_tool("canvas_get_assignments", "Retrieve assignments for a Canvas course.", CourseAssignmentsArgs, assignments),
        make_tool("canvas_get_upcoming_assignments", "Retrieve assignments due within a number of days.", UpcomingArgs, upcoming),
        make_tool("canvas_get_assignment", "Retrieve one Canvas assignment with its description.", AssignmentArgs, assignment),
        make_tool("canvas_get_modules", "Retrieve modules and module items for a Canvas course.", CourseArgs, modules),
        make_tool("canvas_get_course_files", "Retrieve files for a Canvas course.", CourseArgs, files),
    ]
