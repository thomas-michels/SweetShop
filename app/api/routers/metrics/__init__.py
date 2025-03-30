from fastapi import APIRouter
from .query_routers import router as query_router


billing_router = APIRouter()
billing_router.include_router(query_router)
