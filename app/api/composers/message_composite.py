from fastapi import Depends
from app.api.dependencies.get_current_organization import check_current_organization
from app.crud.messages.repositories import MessageRepository
from app.crud.messages.services import MessageServices


async def message_composer(
    organization_id: str = Depends(check_current_organization)
) -> MessageServices:
    message_repository = MessageRepository(organization_id=organization_id)
    message_services = MessageServices(
        message_repository=message_repository,
    )
    return message_services
