from typing import List

from app.crud.sections.repositories import SectionRepository
from app.crud.offers.repositories import OfferRepository
from app.crud.products.repositories import ProductRepository
from app.core.exceptions import UnprocessableEntity

from .repositories import SectionOfferRepository
from .schemas import SectionOffer, SectionOfferInDB, UpdateSectionOffer, CompleteSectionOffer


class SectionOfferServices:
    def __init__(
        self,
        section_offer_repository: SectionOfferRepository,
        section_repository: SectionRepository,
        offer_repository: OfferRepository,
        product_repository: ProductRepository,
    ) -> None:
        self.__section_offer_repository = section_offer_repository
        self.__section_repository = section_repository
        self.__offer_repository = offer_repository
        self.__product_repository = product_repository

    async def create(self, section_offer: SectionOffer) -> SectionOfferInDB:
        await self.__section_repository.select_by_id(id=section_offer.section_id)

        if section_offer.offer_id and section_offer.product_id:
            raise UnprocessableEntity(message="Provide only offerId or productId")

        if section_offer.offer_id:
            await self.__offer_repository.select_by_id(id=section_offer.offer_id)
        elif section_offer.product_id:
            await self.__product_repository.select_by_id(id=section_offer.product_id)
        else:
            raise UnprocessableEntity(message="offerId or productId is required")

        return await self.__section_offer_repository.create(section_offer=section_offer)

    async def update(self, id: str, updated_section_offer: UpdateSectionOffer) -> SectionOfferInDB:
        section_offer_in_db = await self.search_by_id(id=id)

        is_updated = section_offer_in_db.validate_updated_fields(updated_section_offer)

        if is_updated:
            section_offer_in_db = await self.__section_offer_repository.update(section_offer=section_offer_in_db)

        return section_offer_in_db

    async def search_by_id(self, id: str) -> SectionOfferInDB:
        return await self.__section_offer_repository.select_by_id(id=id)

    async def search_all(
        self,
        section_id: str,
        is_visible: bool = None,
        expand: List[str] = [],
    ) -> List[SectionOfferInDB | CompleteSectionOffer]:
        section_offers = await self.__section_offer_repository.select_all(
            section_id=section_id, is_visible=is_visible
        )

        if not expand or not section_offers:
            return section_offers

        complete_section_offers: List[CompleteSectionOffer] = []

        for section_offer in section_offers:
            complete = CompleteSectionOffer.model_validate(section_offer)

            if "offer" in expand and section_offer.offer_id:
                offer_in_db = await self.__offer_repository.select_by_id(
                    id=section_offer.offer_id, raise_404=False
                )
                complete.offer = offer_in_db

            if "product" in expand and section_offer.product_id:
                product_in_db = await self.__product_repository.select_by_id(
                    id=section_offer.product_id, raise_404=False
                )
                complete.product = product_in_db

            complete_section_offers.append(complete)

        return complete_section_offers

    async def delete_by_id(self, id: str) -> SectionOfferInDB:
        return await self.__section_offer_repository.delete_by_id(id=id)
