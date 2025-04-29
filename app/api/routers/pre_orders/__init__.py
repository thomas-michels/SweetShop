from fastapi import APIRouter
from .command_routers import router as command_router
from .query_routers import router as query_router


pre_order_router = APIRouter()
pre_order_router.include_router(command_router)
pre_order_router.include_router(query_router)
