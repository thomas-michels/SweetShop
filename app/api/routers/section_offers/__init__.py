from fastapi import APIRouter
from .command_routers import router as command_router
from .query_routers import router as query_router

section_offer_router = APIRouter()
section_offer_router.include_router(command_router)
section_offer_router.include_router(query_router)
