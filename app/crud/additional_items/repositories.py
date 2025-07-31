from typing import List

from pydantic import ValidationError

from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository
from app.core.utils.utc_datetime import UTCDateTime

from .models import AdditionalItemModel
from .schemas import AdditionalItem, AdditionalItemInDB

_logger = get_logger(__name__)


class AdditionalItemRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.organization_id = organization_id

    def _to_schema(self, model: AdditionalItemModel) -> AdditionalItemInDB:
        data = model.to_mongo().to_dict()
        data["id"] = str(model.id)
        data["created_at"] = model.created_at
        data["updated_at"] = model.updated_at
        return AdditionalItemInDB.model_validate(data)

    async def create(self, additional_id: str, item: AdditionalItem) -> AdditionalItemInDB:
        try:
            model = AdditionalItemModel(
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
                organization_id=self.organization_id,
                additional_id=additional_id,
                **item.model_dump(),
            )
            model.save()
            return self._to_schema(model)
        except Exception as error:
            _logger.error(f"Error on create_additional_item: {error}")
            raise UnprocessableEntity(message="Error on create new additional item")

    async def update(self, item: AdditionalItemInDB) -> AdditionalItemInDB:
        try:
            model: AdditionalItemModel = AdditionalItemModel.objects(
                id=item.id, is_active=True, organization_id=self.organization_id
            ).first()
            data = item.model_dump()
            for field in ["id", "organization_id", "created_at", "_id"]:
                data.pop(field, None)
            model.update(**data)
            return await self.select_by_id(id=item.id)
        except ValidationError:
            raise NotFoundError(message="Additional item not found")
        except Exception as error:
            _logger.error(f"Error on update_additional_item: {error}")
            raise UnprocessableEntity(message="Error on update additional item")

    async def select_by_id(self, id: str, raise_404: bool = True) -> AdditionalItemInDB:
        try:
            model: AdditionalItemModel = AdditionalItemModel.objects(
                id=id, is_active=True, organization_id=self.organization_id
            ).first()
            return self._to_schema(model)
        except Exception as error:
            _logger.error(f"Error on select_by_id: {error}")
            if raise_404:
                raise NotFoundError(message=f"AdditionalItem #{id} not found")

    async def select_all(self, additional_id: str) -> List[AdditionalItemInDB]:
        try:
            results = []
            objects = AdditionalItemModel.objects(
                is_active=True, organization_id=self.organization_id, additional_id=additional_id
            ).order_by("position")
            for model in objects:
                results.append(self._to_schema(model))
            return results
        except Exception as error:
            _logger.error(f"Error on select_all: {error}")
            raise NotFoundError(message="Additional items not found")

    async def delete_by_id(self, id: str) -> AdditionalItemInDB:
        try:
            model: AdditionalItemModel = AdditionalItemModel.objects(
                id=id, is_active=True, organization_id=self.organization_id
            ).first()
            if model:
                model.delete()
                return self._to_schema(model)
            raise NotFoundError(message=f"AdditionalItem #{id} not found")
        except Exception as error:
            _logger.error(f"Error on delete_by_id: {error}")
            raise NotFoundError(message=f"AdditionalItem #{id} not found")
