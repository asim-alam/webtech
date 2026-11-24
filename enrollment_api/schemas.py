from pydantic import BaseModel, Field


class EnrollmentRequest(BaseModel):
    student_id: int = Field(gt=0)
    course_id: int = Field(gt=0)


class EnrollmentResponse(BaseModel):
    id: int
    student_id: int
    course_id: int
