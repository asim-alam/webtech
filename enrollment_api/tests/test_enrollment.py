import pytest
from fastapi.testclient import TestClient
from main import create_app
from repository import EnrollmentRepository


@pytest.fixture
def client():
    # Like a new Postman session, but also starts with clean sample data.
    with TestClient(create_app()) as test_client:
        yield test_client


def test_create_enrollment(client):
    response = client.post("/enrollments", json={"student_id": 1, "course_id": 1})
    assert response.status_code == 201
    assert response.json() == {"id": 1, "student_id": 1, "course_id": 1}
    assert response.headers["Location"] == "/enrollments/1"
    assert response.headers["X-Request-ID"]


def test_read_enrollment(client):
    created = client.post("/enrollments", json={"student_id": 1, "course_id": 1})
    response = client.get(created.headers["Location"])
    assert response.status_code == 200
    assert response.json() == created.json()


def test_cancel_and_restore_seat(client):
    created = client.post("/enrollments", json={"student_id": 1, "course_id": 1})
    url = created.headers["Location"]
    response = client.delete(url)
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(url).status_code == 404
    # The course originally had only one seat. It is available again.
    response = client.post("/enrollments", json={"student_id": 2, "course_id": 1})
    assert response.status_code == 201
    assert response.json()["id"] != created.json()["id"]


def test_course_full(client):
    assert client.post("/enrollments", json={"student_id": 1, "course_id": 1}).status_code == 201
    response = client.post("/enrollments", json={"student_id": 2, "course_id": 1})
    assert response.status_code == 409
    assert response.json()["detail"] == "No seats left in this course"
    assert response.headers["content-type"] == "application/problem+json"


def test_duplicate_enrollment(client):
    data = {"student_id": 1, "course_id": 2}
    assert client.post("/enrollments", json=data).status_code == 201
    response = client.post("/enrollments", json=data)
    assert response.status_code == 409
    assert "already enrolled" in response.json()["detail"]
    # Rejected duplicate does not consume the remaining seat.
    assert client.post("/enrollments", json={"student_id": 2, "course_id": 2}).status_code == 201


def test_unknown_student(client):
    response = client.post("/enrollments", json={"student_id": 99, "course_id": 1})
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"


def test_unknown_course(client):
    response = client.post("/enrollments", json={"student_id": 1, "course_id": 99})
    assert response.status_code == 404
    assert response.json()["detail"] == "Course not found"


def test_invalid_input(client):
    response = client.post("/enrollments", json={"student_id": 0})
    assert response.status_code == 422
    assert response.json()["requestId"] == response.headers["X-Request-ID"]
    fields = [error["field"] for error in response.json()["errors"]]
    assert "body.student_id" in fields
    assert "body.course_id" in fields


def test_unknown_enrollment(client):
    assert client.get("/enrollments/99").status_code == 404
    assert client.delete("/enrollments/99").status_code == 404


def test_unexpected_error_is_hidden(caplog):
    class BrokenRepository(EnrollmentRepository):
        def get_student(self, student_id):
            raise RuntimeError("private failure details")

    with TestClient(create_app(BrokenRepository())) as client:
        response = client.post("/enrollments", json={"student_id": 1, "course_id": 1})
    assert response.status_code == 500
    assert "private failure details" not in response.text
    assert "private failure details" in caplog.text
    assert response.headers["X-Request-ID"] == response.json()["requestId"]
