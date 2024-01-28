from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.api.shared_schemas.responses import MessageResponse
from app.core.exceptions import (
    InvalidPassword,
    NotFoundError,
    UnprocessableEntity,
)


def unprocessable_entity_error_422(request: Request, exc: UnprocessableEntity):
    error = MessageResponse(message=exc.message)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(error.model_dump()),
    )


def not_found_error_404(request: Request, exc: NotFoundError):
    error = MessageResponse(message=exc.message)

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=jsonable_encoder(error.model_dump()),
    )


def generic_error_400(request: Request, exc: InvalidPassword):
    error = MessageResponse(message=exc.message)

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(error.model_dump()),
    )


def generic_error_500(request: Request, exc: Exception):
    """Internal error"""
    error = MessageResponse(message="An unexpected error happen")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder(error.model_dump()),
    )
