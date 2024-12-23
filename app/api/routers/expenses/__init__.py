from fastapi import APIRouter
from .command_routers import router as command_router
from .query_routers import router as query_router


expenses_router = APIRouter()
expenses_router.include_router(command_router)
expenses_router.include_router(query_router)
