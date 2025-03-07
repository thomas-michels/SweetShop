from typing import List

from app.api.dependencies.email_sender import send_email

from .schemas import MarketingEmail, MarketingEmailInDB
from .repositories import MarketingEmailRepository


class MarketingEmailServices:

    def __init__(self, marketing_email_repository: MarketingEmailRepository) -> None:
        self.__marketing_email_repository = marketing_email_repository

    async def create(self, marketing_email: MarketingEmail) -> MarketingEmailInDB:
        marketing_email_in_db = await self.__marketing_email_repository.create(marketing_email=marketing_email)

        with open("./templates/ebook-pascoa.html", mode="r", encoding="UTF-8") as file:
            message = file.read()
            message = message.replace("$CUSTOMER_NAME$", marketing_email_in_db.name)

        send_email(
            email_to=[marketing_email_in_db.email],
            title='Obrigado por adquirir "Os sabores de ovos de Páscoa mais desejados do ano"! 🍫',
            message=message
        )

        return marketing_email_in_db

    async def search_by_id(self, id: str) -> MarketingEmailInDB:
        marketing_email_in_db = await self.__marketing_email_repository.select_by_id(id=id)
        return marketing_email_in_db

    async def search_all(self, query: str) -> List[MarketingEmailInDB]:
        marketing_emails = await self.__marketing_email_repository.select_all(query=query)
        return marketing_emails

    async def delete_by_id(self, id: str) -> MarketingEmailInDB:
        marketing_email_in_db = await self.__marketing_email_repository.delete_by_id(id=id)
        return marketing_email_in_db
