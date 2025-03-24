from typing import List
from app.crud.menus.repositories import MenuRepository
from .schemas import Section, SectionInDB, UpdateSection
from .repositories import SectionRepository


class SectionServices:

    def __init__(
        self,
        section_repository: SectionRepository,
        menu_repository: MenuRepository,
    ) -> None:
        self.__section_repository = section_repository
        self.__menu_repository = menu_repository

    async def create(self, section: Section) -> SectionInDB:
        await self.__menu_repository.select_by_id(id=section.menu_id)

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

    async def search_all(self, menu_id: str, is_visible: bool = None, expand: List[str] = []) -> List[SectionInDB]:
        sections = await self.__section_repository.select_all(
            menu_id=menu_id,
            is_visible=is_visible
        )
        return sections

    async def delete_by_id(self, id: str) -> SectionInDB:
        section_in_db = await self.__section_repository.delete_by_id(id=id)
        return section_in_db
