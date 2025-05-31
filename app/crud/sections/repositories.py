from typing import List

from pydantic import ValidationError

from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository
from app.core.utils.utc_datetime import UTCDateTime

from .models import SectionModel
from .schemas import Section, SectionInDB

_logger = get_logger(__name__)


class SectionRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.organization_id = organization_id

    async def create(self, section: Section) -> SectionInDB:
        try:
            section_model = SectionModel(
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
                organization_id=self.organization_id,
                **section.model_dump(),
            )
            section_model.name = section_model.name.strip().title()
            section_model.description = section_model.description.strip()

            section_model.save()
            _logger.info(
                f"Section {section.name} saved for organization {self.organization_id}"
            )

            return SectionInDB.model_validate(section_model)

        except Exception as error:
            _logger.error(f"Error on create_section: {str(error)}")
            raise UnprocessableEntity(message="Error on create new section")

    async def update(self, section: SectionInDB) -> SectionInDB:
        try:
            section_model: SectionModel = SectionModel.objects(
                id=section.id, is_active=True, organization_id=self.organization_id
            ).first()
            section.name = section.name.strip().title()
            section.description = section.description.strip()

            section_model.update(**section.model_dump())

            return await self.select_by_id(id=section.id)

        except Exception as error:
            _logger.error(f"Error on update_section: {str(error)}")
            raise UnprocessableEntity(message="Error on update section")

    async def select_count(self) -> int:
        try:
            count = SectionModel.objects(
                is_active=True,
                organization_id=self.organization_id,
            ).count()

            return count if count else 0

        except Exception as error:
            _logger.error(f"Error on select_count: {str(error)}")
            return 0

    async def select_by_id(self, id: str, raise_404: bool = True) -> SectionInDB:
        try:
            section_model: SectionModel = SectionModel.objects(
                id=id, is_active=True, organization_id=self.organization_id
            ).first()

            return SectionInDB.model_validate(section_model)

        except ValidationError:
            if raise_404:
                raise NotFoundError(message=f"Section #{id} not found")

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            if raise_404:
                raise NotFoundError(message=f"Section #{id} not found")

    async def select_all(
        self, menu_id: str, is_visible: bool = None
    ) -> List[SectionInDB]:
        try:
            sections = []

            objects = SectionModel.objects(
                is_active=True, organization_id=self.organization_id, menu_id=menu_id
            )

            if is_visible is not None:
                objects = objects.filter(is_visible=is_visible)

            for section_model in objects.order_by("position"):
                sections.append(SectionInDB.model_validate(section_model))

            return sections

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"Sections not found")

    async def delete_by_id(self, id: str) -> SectionInDB:
        try:
            section_model: SectionModel = SectionModel.objects(
                id=id, is_active=True, organization_id=self.organization_id
            ).first()

            if section_model:
                section_model.delete()

                return SectionInDB.model_validate(section_model)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Section #{id} not found")
