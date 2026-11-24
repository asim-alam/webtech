import logging
from uuid import uuid4
from fastapi import Request
from errors import unexpected_error

logger = logging.getLogger("enrollment.http")


async def log_request(request: Request, call_next):
    # Middleware IN: runs before routing and the endpoint handler.
    request.state.request_id = uuid4().hex[:12]

    try:
        # Let FastAPI route, validate, run the handler and build the response.
        response = await call_next(request)
    except Exception:
        response = unexpected_error(request)

    # Middleware OUT: runs after the response has been prepared.
    response.headers["X-Request-ID"] = request.state.request_id
    logger.info("%s %s -> %s [%s]", request.method, request.url.path,
                response.status_code, request.state.request_id)
    return response
