from fastapi import APIRouter
from .command_routers import router as command_router
from .query_routers import router as query_router


term_of_use_router = APIRouter()
term_of_use_router.include_router(command_router)
term_of_use_router.include_router(query_router)
