import logging
from http import HTTPStatus
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from domain import Conflict, NotFound

logger = logging.getLogger("enrollment.errors")


def problem(request, status, title, detail, errors=None):
    """Return a consistent RFC 9457-style error response."""
    body = {
        "type": "about:blank",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": request.url.path,
        "requestId": request.state.request_id,
    }
    if errors is not None:
        body["errors"] = errors
    return JSONResponse(status_code=status, content=body,
                        media_type="application/problem+json")


def unexpected_error(request):
    # Log private details on the server, never in the response.
    logger.exception("Unexpected error [%s]", request.state.request_id)
    return problem(request, 500, "Internal Server Error", "Something went wrong")


def register_error_handlers(app):
    @app.exception_handler(NotFound)
    async def not_found(request, exc):
        return problem(request, 404, "Not Found", str(exc))

    @app.exception_handler(Conflict)
    async def conflict(request, exc):
        return problem(request, 409, "Conflict", str(exc))

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        fields = [{"field": ".".join(map(str, error["loc"])),
                   "message": error["msg"]} for error in exc.errors()]
        return problem(request, 422, "Unprocessable Entity",
                       "Invalid input", fields)

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        response = problem(request, exc.status_code,
                           HTTPStatus(exc.status_code).phrase, str(exc.detail))
        if exc.headers:
            response.headers.update(exc.headers)
        return response
