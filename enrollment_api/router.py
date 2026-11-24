from fastapi import APIRouter, Response
from schemas import EnrollmentRequest, EnrollmentResponse


def create_router(service):
    # APIRouter groups related endpoints. The service is passed in from main.py.
    router = APIRouter()

    # CREATE: enroll a student in a course.
    @router.post("/enrollments", status_code=201, response_model=EnrollmentResponse)
    def enroll(data: EnrollmentRequest, response: Response):
        enrollment = service.enroll(data.student_id, data.course_id)
        response.headers["Location"] = f"/enrollments/{enrollment.id}"
        return enrollment

    # READ: retrieve one enrollment.
    @router.get("/enrollments/{enrollment_id}", response_model=EnrollmentResponse)
    def get_enrollment(enrollment_id: int):
        return service.get_enrollment(enrollment_id)

    # DELETE: cancel an enrollment and restore the seat.
    @router.delete("/enrollments/{enrollment_id}", status_code=204)
    def cancel_enrollment(enrollment_id: int):
        service.cancel(enrollment_id)
        return Response(status_code=204)

    return router
