from typing import List
from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository
from app.core.utils.utc_datetime import UTCDateTime

from .models import MessageModel
from .schemas import Message, MessageInDB

_logger = get_logger(__name__)


class MessageRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.organization_id = organization_id

    async def create(self, message: Message) -> MessageInDB:
        try:
            message_model = MessageModel(
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
                organization_id=self.organization_id,
                **message.model_dump(),
            )

            message_model.save()

            return await self.select_by_id(id=message_model.id)

        except Exception as error:
            _logger.error(f"Error on create_message: {str(error)}")
            raise UnprocessableEntity(message="Error on create message")

    async def update(self, message: MessageInDB) -> MessageInDB:
        try:
            message_model: MessageModel = MessageModel.objects(
                id=message.id, is_active=True, organization_id=self.organization_id
            ).first()

            message_model.update(**message.model_dump())

            return await self.select_by_id(id=message.id)

        except Exception as error:
            _logger.error(f"Error on update_message: {str(error)}")
            raise UnprocessableEntity(message="Error on update message")

    async def select_by_id(self, id: str, raise_404: bool = True) -> MessageInDB:
        try:
            message_model: MessageModel = MessageModel.objects(
                id=id, is_active=True, organization_id=self.organization_id
            ).first()

            if message_model:
                message = MessageInDB.model_validate(message_model)
                return message

            elif raise_404:
                raise NotFoundError(
                    message=f"Message with ID #{id} not found"
                )

        except Exception as error:
            if raise_404:
                raise NotFoundError(
                    message=f"Message with ID #{id} not found"
                )

            _logger.error(f"Error on select_by_id: {str(error)}")

    async def select_all(self, page: int = None, page_size: int = None) -> List[MessageInDB]:
        try:
            messages = []

            objects = MessageModel.objects(
                is_active=True, organization_id=self.organization_id
            )

            skip = (page - 1) * page_size
            objects = objects.order_by("-created_at").skip(skip).limit(page_size)

            for message_model in objects:
                messages.append(MessageInDB.model_validate(message_model))

            return messages

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"Messages not found")

    async def delete_by_id(self, id: str) -> MessageInDB:
        try:
            message_model: MessageModel = MessageModel.objects(
                id=id, is_active=True, organization_id=self.organization_id
            ).first()

            if message_model:
                message_model.delete()

                return MessageInDB.model_validate(message_model)

            raise NotFoundError(message=f"Message with ID #{id} not found")

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Message with ID #{id} not found")
