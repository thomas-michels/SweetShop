from fastapi import APIRouter
from .query_routers import router as query_router


metric_router = APIRouter()
metric_router.include_router(query_router)
