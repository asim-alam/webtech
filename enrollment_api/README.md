# Simple Enrollment API

A small WebTech lab project using FastAPI. Students can enroll in a course, retrieve an enrollment, and cancel it. A course has limited available seats.

## 1. Run the project

Requires Python 3.11 or newer. Tested on Linux with Python 3.13.5.

Open a terminal in this folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

On Windows, use `py -m venv .venv` and `.venv\Scripts\activate` instead of the first two commands. On Linux/Python 3.13, you can install `requirements-lock.txt` instead for the exact dependency versions used in testing.

Open **http://127.0.0.1:8000/docs** in your browser. Swagger UI is included with FastAPI. Click an endpoint, click **Try it out**, enter the data, then click **Execute**. The docs and OpenAPI schema are framework-provided routes, not extra business endpoints.

## 2. Sample data

Students and courses are already in `repository.py`. No database installation is needed.

| Student ID | Name |
| --- | --- |
| 1 | Amina |
| 2 | Rahim |
| 3 | Karim |

| Course ID | Name | Initial seats |
| --- | --- | --- |
| 1 | Web Technology | 1 |
| 2 | Database Systems | 2 |

## 3. The three endpoints

| Method | URL | Purpose | Success |
| --- | --- | --- | --- |
| POST | `/enrollments` | Enroll a student | 201 Created |
| GET | `/enrollments/{enrollment_id}` | Read an enrollment | 200 OK |
| DELETE | `/enrollments/{enrollment_id}` | Cancel an enrollment, restore seat | 204 No Content |

### Demo: focus on POST /enrollments

Send this JSON in Swagger UI or Postman:

```json
{"student_id": 1, "course_id": 1}
```

Expected first response (`201 Created`):

```json
{"id": 1, "student_id": 1, "course_id": 1}
```

The `Location` header is `/enrollments/1`. Try these requests in the following order, on a freshly started server:

1. POST the JSON above: 201. One seat is reserved.
2. POST `{"student_id": 2, "course_id": 1}`: 409, no seats left.
3. GET `/enrollments/1`: 200, the enrollment is found.
4. DELETE `/enrollments/1`: 204, the seat is restored.
5. GET `/enrollments/1`: 404, the enrollment no longer exists.
6. POST `{"student_id": 2, "course_id": 1}`: 201, the seat can be used again.

A duplicate enrollment also returns 409. Unknown student or course returns 404. Missing or non-positive IDs return 422.

## 4. Files and architecture

The project is deliberately flat instead of using many nested folders. Each file has one responsibility.

```text
enrollment_api/
  main.py                    # FastAPI setup and dependency wiring
  router.py                  # APIRouter and three endpoint handlers
  middleware.py              # Incoming and outgoing request processing
  schemas.py                 # Pydantic request and response models
  service.py                 # Enrollment use cases
  repository.py              # In-memory dictionaries, sample data
  domain.py                  # Course, Enrollment, seat rule, domain errors
  errors.py                  # Centralized error handlers and problem JSON
  tests/test_enrollment.py   # Automated API integration tests
  requirements.txt           # Direct dependencies
  requirements-lock.txt      # Tested dependency versions
  .env.example               # Example configuration
  .gitignore
  README.md
```

### Complete request lifecycle of POST /enrollments

This follows the six steps from slide 13 of the lecture:

| Step | Responsible component | What it does |
| --- | --- | --- |
| 1. Parse | Uvicorn and FastAPI/Starlette | Uvicorn parses the HTTP protocol; FastAPI reads and validates the JSON body after matching the route. |
| 2. Middleware in | `middleware.py` | Assign a request ID; call `await call_next(request)`. |
| 3. Route | `router.py` | Match HTTP method and path using APIRouter. |
| 4. Handler | `router.py`, `schemas.py`, `service.py`, `domain.py`, `repository.py` | Validate input, call the use case, apply rules and save. |
| 5. Respond | FastAPI and `router.py` / `errors.py` | Build the JSON response or error and set its status. |
| 6. Middleware out | `middleware.py` | Add the request ID header, log status and return the response. |

The router decorator and the controller function live in the same small file, but middleware and error handling are separate. `main.py` only sets up the app and registers components. No custom HTTP parser is necessary. Authentication, CORS and custom body limits are not implemented in this lab.

```text
Client (Swagger / Postman / TestClient)
    |
    v
Middleware IN (middleware.py): generate request ID
    |
    v
Router (router.py): match POST /enrollments
    |
    v
Pydantic (schemas.py): validate student_id and course_id
    |
    v
Controller enroll() (router.py): call service.enroll(...)
    |
    v
Service (service.py): check student, course and duplicate using repository
    |                  call course.reserve_seat()
    v
Domain (domain.py): reject if no seats; otherwise decrease seats
    |
    v
Repository (repository.py): save Enrollment in dictionary
    |
    v
Controller returns enrollment and Location header
    |
    v
FastAPI serializes response to JSON (201)
    |
    v
Middleware OUT (middleware.py) adds X-Request-ID and logs status; client receives response
```

If a rule fails, the domain or service raises `Conflict` or `NotFound` and a centralized handler in `errors.py` turns it into an error response. Pydantic validation failures use the same error format with field-level messages.

### The controller you should be able to explain

```python
@router.post("/enrollments", status_code=201, response_model=EnrollmentResponse)
def enroll(data: EnrollmentRequest, response: Response):
    enrollment = service.enroll(data.student_id, data.course_id)
    response.headers["Location"] = f"/enrollments/{enrollment.id}"
    return enrollment
```

- `@router.post`: registers the HTTP method and URL on the APIRouter. `main.py` attaches this router to the FastAPI app with `app.include_router(...)`.
- `status_code=201`: tells FastAPI a new resource was created on success.
- `response_model`: specifies which fields are returned and their types.
- `data: EnrollmentRequest`: FastAPI reads the request JSON and Pydantic validates it before the function runs.
- `service.enroll(...)`: performs the use case. The controller does not contain the seat rule or storage code.
- `Location`: tells the client where to retrieve the created resource.
- `return enrollment`: FastAPI serializes the result to JSON.

The service receives its repository through its constructor. `create_app()` constructs and connects them once, which is a simple form of dependency injection. Each test can use a fresh app and repository. The `Lock` in the service keeps two concurrent enrollment requests from reserving the same last seat within one process. You do not need to explain threading in detail for the endpoint demo.

## 5. Automated integration testing

In the activated environment, run the following command from the project folder (a running server is not required):

```bash
python -m pytest -v
```

A test sends HTTP requests using FastAPI's `TestClient`, instead of you doing it in Postman. Assertions check whether the result is correct. Example:

```python
def test_create_enrollment(client):
    response = client.post("/enrollments", json={"student_id": 1, "course_id": 1})
    assert response.status_code == 201
    assert response.json() == {"id": 1, "student_id": 1, "course_id": 1}
    assert response.headers["Location"] == "/enrollments/1"
    assert response.headers["X-Request-ID"]
```

`@pytest.fixture` supplies a new TestClient with fresh dictionaries for every test. Tests run the real middleware, router, validation, service, domain, repository and response handling together in-process. They do not test a network connection or an external database.

| Test | Expected |
| --- | --- |
| Create enrollment | 201, correct body and headers |
| Read enrollment | 200, matches created enrollment |
| Cancel and restore seat | 204, then 404, then new enrollment succeeds |
| Course full | 409 |
| Duplicate enrollment | 409, no extra seat consumed |
| Unknown student | 404 |
| Unknown course | 404 |
| Invalid input | 422, field errors and request ID |
| Unknown enrollment | GET and DELETE return 404 |
| Unexpected failure | 500, private error logged but hidden from client |

## 6. Configuration and logging

`LOG_LEVEL` is read from the environment (default INFO). For example, before starting the server on Linux, run `export LOG_LEVEL=DEBUG`. `.env.example` documents the setting; this minimal version does not automatically load `.env` files. The middleware generates a request ID, includes it in responses, and logs the method, path and status. Services log enrollment creation and cancellation. Errors use `application/problem+json` with a consistent structure. No secrets are needed.

## 7. Tutorial alignment and what to study

- [Tech With Tim: How To Create a Python API With FastAPI](https://www.youtube.com/watch?v=lWsGhG6N_1E): focus on Pydantic (09:00), POST (12:02), GET (13:39), path parameters (15:57), DELETE (20:30), and manual API testing (22:10). The same core patterns are used here, with the use case and dictionary storage moved into separate files.
- [Ssali Jonathan: Testing A FastAPI App With Pytest](https://www.youtube.com/watch?v=gop9Or2V_80): focus on test setup (04:49), TestClient fixture (05:50), first test (10:00). The test file follows those basic concepts.
- [Official FastAPI testing documentation](https://fastapi.tiangolo.com/tutorial/testing/).

Suggested reading order: `router.py` (three endpoint functions), `schemas.py`, `service.py`, `domain.py`, `repository.py`, then `tests/test_enrollment.py`. Read `middleware.py`, `errors.py` and finally `main.py` to see how everything is connected. The tutorials' published topics and timestamps were used as a guide; this is an original implementation, not a line-by-line copy of the video code.

## 8. Scope and limitations

The project honors the requested maximum of three business endpoints. It demonstrates create, read and delete, not full CRUD: there is no update operation, list operation or separate student/course management API. Students and courses are fixed sample data. The lecture's two-resource create/read/list requirement is therefore not fully met. Confirm the smaller scope with your instructor if the full lecture rubric applies. To meet full CRUD, at minimum another update endpoint is needed, plus the separate resource operations required by the rubric.

The dictionaries reset whenever the server process restarts. This is intentional for a short learning task and is not a production enrollment system. There is no authentication, persistent database, or multi-process state sharing. The tests were run in an existing Python environment, not a fresh virtual environment. A Git repository and meaningful commits need to be created by the student if required by the submission rubric.

**AI-use disclosure:** ChatGPT generated and refactored the starter implementation, tests and README, and ran the automated tests in its environment. Before submission, run the code yourself, inspect the three endpoints and their layers, and record what you personally verified or changed. Do not claim manual verification you have not performed.
