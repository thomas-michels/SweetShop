from typing import List

from app.crud.sections.repositories import SectionRepository
from app.crud.offers.services import OfferServices
from app.crud.products.services import ProductServices
from app.core.exceptions import UnprocessableEntity

from .repositories import SectionItemRepository
from .schemas import SectionItem, SectionItemInDB, UpdateSectionItem, CompleteSectionItem, ItemType


class SectionItemServices:
    def __init__(
        self,
        section_item_repository: SectionItemRepository,
        section_repository: SectionRepository,
        offer_service: OfferServices,
        product_service: ProductServices,
    ) -> None:
        self.__section_item_repository = section_item_repository
        self.__section_repository = section_repository
        self.__offer_service = offer_service
        self.__product_service = product_service
    async def create(self, section_item: SectionItem) -> SectionItemInDB:
        await self.__section_repository.select_by_id(id=section_item.section_id)

        if section_item.item_type == ItemType.OFFER:
            await self.__offer_service.search_by_id(id=section_item.item_id)
        elif section_item.item_type == ItemType.PRODUCT:
            await self.__product_service.search_by_id(id=section_item.item_id)
        else:
            raise UnprocessableEntity(message="Invalid item type")

        return await self.__section_item_repository.create(section_item=section_item)

    async def update(self, id: str, updated_section_item: UpdateSectionItem) -> SectionItemInDB:
        section_item_in_db = await self.search_by_id(id=id)

        is_updated = section_item_in_db.validate_updated_fields(updated_section_item)

        if is_updated:
            section_item_in_db = await self.__section_item_repository.update(section_item=section_item_in_db)

        return section_item_in_db

    async def search_by_id(self, id: str) -> SectionItemInDB:
        return await self.__section_item_repository.select_by_id(id=id)

    async def search_all(
        self,
        section_id: str,
        is_visible: bool = None,
        expand: List[str] = [],
    ) -> List[SectionItemInDB | CompleteSectionItem]:
        section_items = await self.__section_item_repository.select_all(
            section_id=section_id, is_visible=is_visible
        )

        if not expand or not section_items:
            return section_items

        complete_section_items: List[CompleteSectionItem] = []

        for section_item in section_items:
            complete = CompleteSectionItem.model_validate(section_item)

            if "items" in expand:
                if section_item.item_type == ItemType.OFFER:
                    complete.offer = await self.__offer_service.search_by_id(
                        id=section_item.item_id,
                        expand=expand,
                    )

                elif section_item.item_type == ItemType.PRODUCT:
                    complete.product = await self.__product_service.search_by_id(
                        id=section_item.item_id,
                        expand=expand,
                    )

            complete_section_items.append(complete)

        return complete_section_items

    async def delete_by_id(self, id: str) -> SectionItemInDB:
        return await self.__section_item_repository.delete_by_id(id=id)
