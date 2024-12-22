from fastapi import APIRouter
from .command_routers import router as command_router
from .query_routers import router as query_router


fast_order_router = APIRouter()
fast_order_router.include_router(command_router)
fast_order_router.include_router(query_router)
