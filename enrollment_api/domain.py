from dataclasses import dataclass


class NotFound(Exception):
    pass


class Conflict(Exception):
    pass


@dataclass
class Course:
    id: int
    name: str
    seats: int  # Available seats, not total capacity

    def reserve_seat(self):
        if self.seats == 0:
            raise Conflict("No seats left in this course")
        self.seats -= 1

    def release_seat(self):
        self.seats += 1


@dataclass
class Enrollment:
    id: int
    student_id: int
    course_id: int
