import logging
import os
from fastapi import FastAPI
from repository import EnrollmentRepository
from service import EnrollmentService
from router import create_router
from middleware import log_request
from errors import register_error_handlers


def create_app(repository=None):
    # Create the application and connect its components in one place.
    app = FastAPI(title="Simple Enrollment API")
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

    if repository is None:
        repository = EnrollmentRepository()
    service = EnrollmentService(repository)

    app.middleware("http")(log_request)
    register_error_handlers(app)
    app.include_router(create_router(service))
    return app


app = create_app()
