from datetime import datetime
from mongoengine.errors import NotUniqueError
from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository

from .models import TermOfUseAcceptanceModel
from .schemas import TermOfUseAcceptance, TermOfUseAcceptanceInDB

_logger = get_logger(__name__)


class TermOfUseAcceptanceRepository(Repository):
    async def create(self, term_of_use_acceptance: TermOfUseAcceptance) -> TermOfUseAcceptanceInDB:
        try:
            term_of_use_acceptance_model = TermOfUseAcceptanceModel(
                created_at=datetime.now(),
                updated_at=datetime.now(),
                **term_of_use_acceptance.model_dump()
            )
            term_of_use_acceptance_model.save()

            return await self.select_by_id(id=term_of_use_acceptance_model.id)

        except NotUniqueError:
            _logger.warning(f"TermOfUseAcceptance already accepted for user {term_of_use_acceptance.user_id}")
            return await self.select_by_id(id=term_of_use_acceptance_model.id)

        except Exception as error:
            _logger.error(f"Error on create_term_of_use_acceptance: {str(error)}")
            raise UnprocessableEntity(message="Error on create new TermOfUseAcceptance")

    async def select_by_id(self, id: str) -> TermOfUseAcceptanceInDB:
        try:
            term_of_use_acceptance_model: TermOfUseAcceptanceModel = TermOfUseAcceptanceModel.objects(
                id=id,
                is_active=True,
            ).first()

            return TermOfUseAcceptanceInDB.model_validate(term_of_use_acceptance_model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            raise NotFoundError(message=f"TermOfUseAcceptance #{id} not found")

    async def select_by_term_and_user(self, term_of_use_id: str, user_id: str) -> TermOfUseAcceptanceInDB:
        try:
            term_of_use_acceptance_model: TermOfUseAcceptanceModel = TermOfUseAcceptanceModel.objects(
                term_of_use_id=term_of_use_id,
                user_id=user_id,
                is_active=True,
            ).first()

            if term_of_use_acceptance_model:
                return TermOfUseAcceptanceInDB.model_validate(term_of_use_acceptance_model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")

    async def delete(self, acceptance: TermOfUseAcceptanceInDB) -> TermOfUseAcceptanceInDB:
        try:
            term_of_use_acceptance_model: TermOfUseAcceptanceModel = TermOfUseAcceptanceModel.objects(
                id=acceptance.id,
                is_active=True,
            ).first()

            term_of_use_acceptance_model.extra_data = acceptance.extra_data
            term_of_use_acceptance_model.is_active = False

            term_of_use_acceptance_model.update()

            return TermOfUseAcceptanceInDB.model_validate(term_of_use_acceptance_model)

        except Exception as error:
            _logger.error(f"Error on delete: {str(error)}")
            raise NotFoundError(message=f"TermOfUseAcceptance #{id} not found")
