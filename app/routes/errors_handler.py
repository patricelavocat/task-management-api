"""Handle all API errors/exceptions"""

import logging

from fastapi import FastAPI, Request, Response
from sqlalchemy.exc import IntegrityError
from starlette import status
from starlette.responses import JSONResponse

from app.exceptions.app_exceptions import (
    ObjNotFoundException,
)

# pylint: disable=unused-argument
logger = logging.getLogger(__name__)


def add_all_errors_handlers(app: FastAPI) -> None:
    """Add all errors handlers to app.
    Args:
       app (FastAPI): fastAPI app
    """
    all_exception_handlers = [
        (ObjNotFoundException, _handle_db_not_found_exceptions),
        (IntegrityError, _handle_db_action_exceptions),
        (Exception, _handle_unhandled_exceptions),
    ]
    for custom_exception, custom_handler in all_exception_handlers:
        app.add_exception_handler(custom_exception, custom_handler)  # type: ignore


def _handle_db_not_found_exceptions(request: Request, exception: ObjNotFoundException) -> Response:
    """Handle all "ObjNotFoundException" exceptions, for user friendly response
    Args:
        exception (ObjNotFoundException): Caught exception
    Returns:
        Response: Https response, with the related status code
    """
    logger.error(exception)
    return JSONResponse(
        content={"error": "Object not found"},
        status_code=status.HTTP_404_NOT_FOUND,
    )


def _handle_db_action_exceptions(request: Request, exception: IntegrityError) -> Response:
    """Handle all "IntegrityError" exceptions, for user friendly response
    Args:
        exception (IntegrityError): Caught exception
    Returns:
        Response: Https response, with the related status code
    """
    logger.error(exception)
    return JSONResponse(
        content={"error": "Cannot do this action"},
        status_code=status.HTTP_400_BAD_REQUEST,
    )


def _handle_unhandled_exceptions(request: Request, exception: Exception) -> Response:
    """Handle all unhandled exceptions, for user friendly response
    Args:
        exception (Exception): Caught exception
    Returns:
        Response: Https response, with the related status code
    """
    logger.error(exception, exc_info=True)
    return JSONResponse(
        content={"error": "Internal error"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
