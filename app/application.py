from fastapi import FastAPI
from app.api.routers import user_router
from app.api.routers.exception_handlers import (
    unprocessable_entity_error_422,
    generic_error_500,
    not_found_error_404,
    generic_error_400
)
from app.core.db import lifespan
from app.core.exceptions import (
    UnprocessableEntity,
    NotFoundError,
    InvalidPassword
)
from app.core.configs import get_environment

_env = get_environment()


app = FastAPI(
    title=_env.APPLICATION_NAME,
    lifespan=lifespan
)

app.include_router(user_router, prefix="/api")

app.add_exception_handler(UnprocessableEntity, unprocessable_entity_error_422)
app.add_exception_handler(NotFoundError, not_found_error_404)
app.add_exception_handler(InvalidPassword, generic_error_400)
app.add_exception_handler(Exception, generic_error_500)


@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"message": "I'm alive"}
