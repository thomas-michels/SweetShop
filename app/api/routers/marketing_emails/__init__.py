from fastapi import APIRouter
from .command_routers import router as command_router


marketing_email_router = APIRouter()
marketing_email_router.include_router(command_router)
