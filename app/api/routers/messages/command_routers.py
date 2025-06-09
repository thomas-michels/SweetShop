from fastapi import APIRouter, Depends, Header, BackgroundTasks
from app.api.composers import message_composer
from app.api.dependencies import build_response
from app.crud.messages import (
    Message,
    MessageInDB,
    MessageServices
)
from app.core.configs import get_environment

router = APIRouter(tags=["Messages"])
_env = get_environment()


@router.post("/messages", responses={201: {"model": MessageInDB}})
async def create_message(
    message: Message,
    worker: BackgroundTasks,
    message_services: MessageServices = Depends(message_composer),
    token: str = Header(default=None, include_in_schema=False)
):
    if _env.API_TOKEN != token:
        return build_response(
            status_code=401, message="Unauthorized!", data=None
        )

    worker.add_task(message_services.create, message)

    return build_response(
        status_code=202, message="Message will be created soon", data=None
    )
