from typing import List

from app.api.dependencies.whats_app_adapter import WhatsAppMessageSender

from .repositories import MessageRepository
from .schemas import MessageInDB, Message


class MessageServices:

    def __init__(
        self,
        message_repository: MessageRepository,
    ) -> None:
        self.__message_repository = message_repository
        self.__message_sender = WhatsAppMessageSender()

    async def create(self, message: Message) -> MessageInDB:
        full_number = f"{message.international_code}{message.ddd}{message.phone_number}"

        if not self.__message_sender.check_whatsapp_numbers(number=full_number):
            return

        whats_message = self.__message_sender.send_message(
            number=full_number,
            message=message.message
        )

        if not whats_message:
            return

        whats_message_id = whats_message["key"]["id"]
        message.integration_id = whats_message_id

        message_in_db = await self.__message_repository.create(message=message)

        return message_in_db

    async def search_by_id(self, id: str) -> MessageInDB:
        message_in_db = await self.__message_repository.select_by_id(id=id)
        return message_in_db

    async def search_all(
        self,
        page: int = None,
        page_size: int = None
    ) -> List[MessageInDB]:
        messages = await self.__message_repository.select_all(
            page=page,
            page_size=page_size
        )

        return messages

    async def delete_by_id(self, id: str) -> MessageInDB:
        message_in_db = await self.__message_repository.delete_by_id(id=id)
        return message_in_db
