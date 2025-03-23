from typing import List
from app.api.dependencies.get_plan_feature import get_plan_feature
from app.api.exceptions.authentication_exceptions import UnauthorizedException
from app.core.utils.features import Feature
from .schemas import Section, SectionInDB, UpdateSection
from .repositories import SectionRepository


class SectionServices:

    def __init__(
        self,
        section_repository: SectionRepository,
    ) -> None:
        self.__section_repository = section_repository

    async def create(self, section: Section) -> SectionInDB:
        plan_feature = await get_plan_feature(
            organization_id=self.__section_repository.organization_id,
            feature_name=Feature.DISPLAY_MENU
        )

        if not plan_feature or not plan_feature.value.startswith("t"):
            raise UnauthorizedException(detail=f"You cannot access this feature")

        section_in_db = await self.__section_repository.create(section=section)
        return section_in_db

    async def update(self, id: str, updated_section: UpdateSection) -> SectionInDB:
        section_in_db = await self.search_by_id(id=id)

        is_updated = section_in_db.validate_updated_fields(update_section=updated_section)

        if is_updated:
            section_in_db = await self.__section_repository.update(section=section_in_db)

        return section_in_db

    async def search_count(self) -> int:
        return await self.__section_repository.select_count()

    async def search_by_id(self, id: str) -> SectionInDB:
        section_in_db = await self.__section_repository.select_by_id(id=id)
        return section_in_db

    async def search_all(self, query: str, expand: List[str] = []) -> List[SectionInDB]:
        sections = await self.__section_repository.select_all(
            query=query,
        )
        return sections

    async def delete_by_id(self, id: str) -> SectionInDB:
        section_in_db = await self.__section_repository.delete_by_id(id=id)
        return section_in_db
