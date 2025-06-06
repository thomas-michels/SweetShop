from fastapi import APIRouter
from .command_routers import router as command_router
from .query_routers import router as query_router


offer_router = APIRouter()
offer_router.include_router(command_router)
offer_router.include_router(query_router)
