from fastapi import APIRouter
from .command_routers import router as command_router
from .query_routers import router as query_router


coupon_router = APIRouter()
coupon_router.include_router(command_router)
coupon_router.include_router(query_router)
