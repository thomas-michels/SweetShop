from typing import List
from mongoengine.errors import NotUniqueError
from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository

from .models import MarketingEmailModel
from .schemas import MarketingEmail, MarketingEmailInDB

_logger = get_logger(__name__)


class MarketingEmailRepository(Repository):
    async def create(self, marketing_email: MarketingEmail) -> MarketingEmailInDB:
        try:
            marketing_email_model = MarketingEmailModel(
                **marketing_email.model_dump()
            )
            marketing_email_model.save()

            return await self.select_by_id(id=marketing_email_model.id)

        except NotUniqueError:
            _logger.warning(f"MarketingEmail with email {marketing_email.email} is not unique")
            raise UnprocessableEntity(message="Email already used")

        except Exception as error:
            _logger.error(f"Error on create_marketing_email: {str(error)}")
            raise UnprocessableEntity(message="Error on create new MarketingEmail")

    async def select_by_id(self, id: str, raise_404: bool = True) -> MarketingEmailInDB:
        try:
            marketing_email_model: MarketingEmailModel = MarketingEmailModel.objects(
                id=id,
            ).first()

            return MarketingEmailInDB.model_validate(marketing_email_model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            if raise_404:
                raise NotFoundError(message=f"MarketingEmail #{id} not found")

    async def select_all(self, query: str) -> List[MarketingEmailInDB]:
        try:
            marketing_emails = []

            objects = MarketingEmailModel.objects()

            if query:
                objects = objects.filter(name__iregex=query)

            for marketing_email_model in objects.order_by("name"):
                marketing_emails.append(MarketingEmailInDB.model_validate(marketing_email_model))

            return marketing_emails

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"MarketingEmails not found")

    async def delete_by_id(self, id: str) -> MarketingEmailInDB:
        try:
            marketing_email_model: MarketingEmailModel = MarketingEmailModel.objects(
                id=id,
            ).first()
            marketing_email_model.delete()

            return MarketingEmailInDB.model_validate(marketing_email_model)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"MarketingEmail #{id} not found")
