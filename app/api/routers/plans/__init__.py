from fastapi import APIRouter
from .command_routers import router as command_router
from .query_routers import router as query_router


plan_router = APIRouter()
plan_router.include_router(command_router)
plan_router.include_router(query_router)
