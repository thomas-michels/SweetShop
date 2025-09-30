from fastapi import APIRouter

from .command_routers import router as command_router
from .query_routers import router as query_router


notification_router = APIRouter()
notification_router.include_router(command_router)
notification_router.include_router(query_router)
