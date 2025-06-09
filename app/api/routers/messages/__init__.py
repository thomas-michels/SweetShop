from fastapi import APIRouter
from .command_routers import router as command_router


message_router = APIRouter()
message_router.include_router(command_router)
