from datetime import datetime
from typing import List
from mongoengine.errors import NotUniqueError
from app.api.exceptions.authentication_exceptions import BadRequestException
from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository

from .models import TermOfUseModel
from .schemas import TermOfUse, TermOfUseInDB

_logger = get_logger(__name__)


class TermOfUseRepository(Repository):
    async def create(self, term_of_use: TermOfUse) -> TermOfUseInDB:
        try:
            term_of_use_model = TermOfUseModel(
                created_at=datetime.now(),
                updated_at=datetime.now(),
                **term_of_use.model_dump()
            )
            term_of_use_model.save()

            return await self.select_by_id(id=term_of_use_model.id)

        except NotUniqueError:
            _logger.warning(f"TermOfUse with hash {term_of_use.hash} or version {term_of_use.version} are not unique")
            raise BadRequestException(message="Hash or version are not unique")

        except Exception as error:
            _logger.error(f"Error on create_term_of_use: {str(error)}")
            raise UnprocessableEntity(message="Error on create new TermOfUse")

    async def select_by_id(self, id: str) -> TermOfUseInDB:
        try:
            term_of_use_model: TermOfUseModel = TermOfUseModel.objects(
                id=id,
                is_active=True,
            ).first()

            return TermOfUseInDB.model_validate(term_of_use_model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            raise NotFoundError(message=f"TermOfUse #{id} not found")

    async def select_by_hash(self, hash: str) -> TermOfUseInDB:
        try:
            term_of_use_model: TermOfUseModel = TermOfUseModel.objects(
                hash=hash
            ).first()

            if term_of_use_model:
                return TermOfUseInDB.model_validate(term_of_use_model)

        except Exception as error:
            _logger.error(f"Error on select_by_hash: {str(error)}")

    async def select_all(self) -> List[TermOfUseInDB]:
        try:
            term_of_uses = []

            objects = TermOfUseModel.objects(
                is_active=True
            )

            for term_of_use_model in objects.order_by("-created_at"):
                term_of_uses.append(TermOfUseInDB.model_validate(term_of_use_model))

            return term_of_uses

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"TermOfUses not found")

    async def delete_by_id(self, id: str) -> TermOfUseInDB:
        try:
            term_of_use_model: TermOfUseModel = TermOfUseModel.objects(
                id=id,
                is_active=True,
            ).first()
            term_of_use_model.delete()

            return TermOfUseInDB.model_validate(term_of_use_model)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"TermOfUse #{id} not found")
