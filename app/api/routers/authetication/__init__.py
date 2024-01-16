from fastapi import APIRouter
from .login_routers import router as login_router


authentication_router = APIRouter()
authentication_router.include_router(login_router)
