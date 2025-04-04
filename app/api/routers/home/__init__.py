from fastapi import APIRouter
from .query_routers import router as query_router


home_router = APIRouter()
home_router.include_router(query_router)
