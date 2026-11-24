from domain import Course, Enrollment


class EnrollmentRepository:
    """In-memory storage. A new repository starts with fresh sample data."""

    def __init__(self):
        self.students = {1: "Amina", 2: "Rahim", 3: "Karim"}
        self.courses = {
            1: Course(1, "Web Technology", 1),
            2: Course(2, "Database Systems", 2),
        }
        self.enrollments = {}
        self.next_id = 1

    def get_student(self, student_id):
        return self.students.get(student_id)

    def get_course(self, course_id):
        return self.courses.get(course_id)

    def find_enrollment(self, student_id, course_id):
        for enrollment in self.enrollments.values():
            if (enrollment.student_id == student_id
                    and enrollment.course_id == course_id):
                return enrollment
        return None

    def add(self, student_id, course_id):
        enrollment = Enrollment(self.next_id, student_id, course_id)
        self.enrollments[enrollment.id] = enrollment
        self.next_id += 1
        return enrollment

    def get(self, enrollment_id):
        return self.enrollments.get(enrollment_id)

    def delete(self, enrollment_id):
        del self.enrollments[enrollment_id]
