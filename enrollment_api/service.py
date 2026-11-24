import logging
from threading import Lock
from domain import NotFound, Conflict

logger = logging.getLogger(__name__)


class EnrollmentService:
    def __init__(self, repository):
        self.repository = repository
        self.lock = Lock()

    def enroll(self, student_id, course_id):
        # Keep checking and reserving a seat together, even for concurrent requests.
        with self.lock:
            if self.repository.get_student(student_id) is None:
                raise NotFound("Student not found")

            course = self.repository.get_course(course_id)
            if course is None:
                raise NotFound("Course not found")

            if self.repository.find_enrollment(student_id, course_id):
                raise Conflict("Student is already enrolled in this course")

            course.reserve_seat()
            enrollment = self.repository.add(student_id, course_id)
            logger.info("Enrollment created id=%s", enrollment.id)
            return enrollment

    def get_enrollment(self, enrollment_id):
        enrollment = self.repository.get(enrollment_id)
        if enrollment is None:
            raise NotFound("Enrollment not found")
        return enrollment

    def cancel(self, enrollment_id):
        with self.lock:
            enrollment = self.get_enrollment(enrollment_id)
            course = self.repository.get_course(enrollment.course_id)
            self.repository.delete(enrollment_id)
            course.release_seat()
            logger.info("Enrollment cancelled id=%s", enrollment_id)
