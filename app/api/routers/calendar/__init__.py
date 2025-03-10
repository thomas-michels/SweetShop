from fastapi import APIRouter
from .query_routers import router as query_router


calendar_router = APIRouter()
calendar_router.include_router(query_router)
