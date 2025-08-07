from typing import List

from pydantic import ValidationError

from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository
from app.core.utils.utc_datetime import UTCDateTime

from .models import SectionItemModel
from .schemas import SectionItem, SectionItemInDB, ItemType

_logger = get_logger(__name__)


class SectionItemRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.organization_id = organization_id

    async def create(self, section_item: SectionItem) -> SectionItemInDB:
        try:
            model = SectionItemModel(
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
                organization_id=self.organization_id,
                **section_item.model_dump(),
            )

            model.save()
            return SectionItemInDB.model_validate(model)

        except Exception as error:
            _logger.error(f"Error on create_section_item: {error}")
            raise UnprocessableEntity(message="Error on create new section item")

    async def update(self, section_item: SectionItemInDB) -> SectionItemInDB:
        try:
            model: SectionItemModel = SectionItemModel.objects(
                id=section_item.id, is_active=True, organization_id=self.organization_id
            ).first()

            model.update(**section_item.model_dump())

            return await self.select_by_id(id=section_item.id)

        except ValidationError:
            raise NotFoundError(message="Section item not found")

        except Exception as error:
            _logger.error(f"Error on update_section_item: {error}")
            raise UnprocessableEntity(message="Error on update section item")

    async def select_by_id(self, id: str, raise_404: bool = True) -> SectionItemInDB:
        try:
            model: SectionItemModel = SectionItemModel.objects(
                id=id, is_active=True, organization_id=self.organization_id
            ).first()
            return SectionItemInDB.model_validate(model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {error}")
            if raise_404:
                raise NotFoundError(message=f"SectionItem #{id} not found")

    async def select_all(self, section_id: str, is_visible: bool = None) -> List[SectionItemInDB]:
        try:
            results = []

            objects = SectionItemModel.objects(
                is_active=True, organization_id=self.organization_id, section_id=section_id
            )

            if is_visible is not None:
                objects = objects.filter(is_visible=is_visible)

            for model in objects.order_by("position"):
                results.append(SectionItemInDB.model_validate(model))

            return results

        except Exception as error:
            _logger.error(f"Error on select_all: {error}")
            raise NotFoundError(message="Section items not found")

    async def delete_by_id(self, id: str) -> SectionItemInDB:
        try:
            model: SectionItemModel = SectionItemModel.objects(
                id=id, is_active=True, organization_id=self.organization_id
            ).first()

            if model:
                model.delete()
                return SectionItemInDB.model_validate(model)

            raise NotFoundError(message=f"SectionItem #{id} not found")

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {error}")
            raise NotFoundError(message=f"SectionItem #{id} not found")

    async def delete_by_item_id(self, item_id: str, item_type: ItemType) -> None:
        try:
            objects = SectionItemModel.objects(
                item_id=item_id,
                item_type=item_type.value,
                is_active=True,
                organization_id=self.organization_id,
            )

            for model in objects:
                model.delete()

        except Exception as error:
            _logger.error(f"Error on delete_by_item_id: {error}")
