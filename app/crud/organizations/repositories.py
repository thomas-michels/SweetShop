from datetime import datetime
from typing import List
from fastapi.encoders import jsonable_encoder
from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository

from .models import OrganizationModel
from .schemas import Organization, OrganizationInDB

_logger = get_logger(__name__)


class OrganizationRepository(Repository):
    def __init__(self) -> None:
        super().__init__()

    async def create(self, organization: Organization) -> OrganizationInDB:
        try:
            json = jsonable_encoder(organization.model_dump())

            organization_model = OrganizationModel(
                is_active=True,
                users={},
                created_at=datetime.now(),
                updated_at=datetime.now(),
                **json
            )

            organization_model.save()

            return OrganizationInDB.model_validate(organization_model)

        except Exception as error:
            _logger.error(f"Error on create_organization: {str(error)}")
            raise UnprocessableEntity(message="Error on create new organization")

    async def update(self, organization_id: str, organization: dict) -> OrganizationInDB:
        try:
            organization_model: OrganizationModel = OrganizationModel.objects(id=organization_id, is_active=True).first()

            organization_model.update(**organization)
            organization_model.save()

            return await self.select_by_id(id=organization_id)

        except Exception as error:
            _logger.error(f"Error on update_organization: {str(error)}")
            raise UnprocessableEntity(message="Error on update organization")

    async def select_by_id(self, id: str) -> OrganizationInDB:
        try:
            organization_model: OrganizationModel = OrganizationModel.objects(id=id, is_active=True).first()

            return OrganizationInDB.model_validate(organization_model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            raise NotFoundError(message=f"Organization #{id} not found")

    async def select_all(self) -> List[OrganizationInDB]:
        try:
            organizations = []

            objects = OrganizationModel.objects(is_active=True)

            for organization_model in objects:
                organizations.append(OrganizationInDB.model_validate(organization_model))

            return organizations

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"Organizations not found")

    async def delete_by_id(self, id: str) -> OrganizationInDB:
        try:
            organization_model: OrganizationModel = OrganizationModel.objects(id=id, is_active=True).first()
            organization_model.delete()

            return OrganizationInDB.model_validate(organization_model)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Organization #{id} not found")