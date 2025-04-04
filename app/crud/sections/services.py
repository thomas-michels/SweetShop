from typing import List
from app.crud.offers.services import OfferServices
from app.crud.menus.repositories import MenuRepository
from .repositories import SectionRepository
from .schemas import CompleteSection, Section, SectionInDB, UpdateSection


class SectionServices:

    def __init__(
        self,
        section_repository: SectionRepository,
        menu_repository: MenuRepository,
        offer_service: OfferServices,
    ) -> None:
        self.__section_repository = section_repository
        self.__menu_repository = menu_repository
        self.__offer_service = offer_service

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

    async def search_by_id(self, id: str, expand: List[str] = []) -> SectionInDB:
        section_in_db = await self.__section_repository.select_by_id(id=id)

        if not expand or not section_in_db:
            return section_in_db

        sections = await self.__build_complete_section(sections=[section_in_db], expand=expand)
        return sections[0]

    async def search_all(self, menu_id: str, is_visible: bool = None, expand: List[str] = []) -> List[SectionInDB]:
        sections = await self.__section_repository.select_all(
            menu_id=menu_id,
            is_visible=is_visible
        )

        if not expand or not sections:
            return sections

        return await self.__build_complete_section(sections=sections, is_visible=is_visible, expand=expand)

    async def delete_by_id(self, id: str) -> SectionInDB:
        section_in_db = await self.__section_repository.delete_by_id(id=id)
        return section_in_db

    async def __build_complete_section(self, sections: List[SectionInDB], is_visible: bool, expand: List[str]) -> CompleteSection:
        complete_sections = []

        for section in sections:
            complete_section = CompleteSection.model_validate(section)

            if "offers" in expand:
                offers = await self.__offer_service.search_all(
                    section_id=section.id,
                    is_visible=is_visible,
                    expand=expand
                )
                complete_section.offers = offers

            complete_sections.append(complete_section)

        return complete_sections
