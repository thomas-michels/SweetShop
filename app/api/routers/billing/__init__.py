from fastapi import APIRouter
from .query_routers import router as query_router


financial_router = APIRouter()
financial_router.include_router(query_router)
