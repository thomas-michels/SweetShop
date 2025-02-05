from fastapi import APIRouter
from .query_routers import router as query_router


mercado_pago_router = APIRouter()
mercado_pago_router.include_router(query_router)
