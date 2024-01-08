from fastapi import FastAPI

from app.core.configs import get_environment

_env = get_environment()


app = FastAPI(
    title=_env.APPLICATION_NAME
)

@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"message": "I'm alive"}
