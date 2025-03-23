from fastapi import APIRouter
from .command_routers import router as command_router
from .query_routers import router as query_router


file_router = APIRouter()
file_router.include_router(command_router)
file_router.include_router(query_router)
