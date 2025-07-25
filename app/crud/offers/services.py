from typing import List

from app.crud.files.repositories import FileRepository
from app.crud.products.repositories import ProductRepository
from app.crud.products.schemas import (
    CompleteItem,
    CompleteProductSection,
    ProductInDB,
)
from app.crud.sections.repositories import SectionRepository

from .repositories import OfferRepository
from .schemas import CompleteOffer, CompleteOfferProduct, OfferProduct, RequestOffer, Offer, OfferInDB, UpdateOffer


class OfferServices:

    def __init__(
        self,
        offer_repository: OfferRepository,
        section_repository: SectionRepository,
        product_repository: ProductRepository,
        file_repository: FileRepository
    ) -> None:
        self.__offer_repository = offer_repository
        self.__section_repository = section_repository
        self.__product_repository = product_repository
        self.__file_repository = file_repository

    async def create(self, request_offer: RequestOffer) -> OfferInDB:
        await self.__section_repository.select_by_id(id=request_offer.section_id)

        total_cost, total_price, products = await self.__create_offer_product(
            product_ids=request_offer.products
        )

        offer = Offer(
            section_id=request_offer.section_id,
            name=request_offer.name,
            description=request_offer.description,
            is_visible=request_offer.is_visible,
            unit_price=total_price,
            unit_cost=total_cost,
            products=products
        )

        offer_in_db = await self.__offer_repository.create(offer=offer)

        return offer_in_db

    async def update(self, id: str, updated_offer: UpdateOffer) -> OfferInDB:
        offer_in_db = await self.search_by_id(id=id)

        is_updated = offer_in_db.validate_updated_fields(update_offer=updated_offer)

        if is_updated:
            if updated_offer.products is not None:
                total_cost, total_price, products = await self.__create_offer_product(
                    product_ids=updated_offer.products
                )

                offer_in_db.unit_cost = total_cost
                offer_in_db.unit_price = total_price
                offer_in_db.products = products

            offer_in_db = await self.__offer_repository.update(offer=offer_in_db)

        return offer_in_db

    async def search_by_id(self, id: str, expand: List[str] = []) -> OfferInDB:
        offer_in_db = await self.__offer_repository.select_by_id(id=id)

        if not expand or not offer_in_db:
            return offer_in_db

        offers = await self.__build_complete_offer(offers=[offer_in_db], expand=expand)
        return offers[0]

    async def search_all(self, section_id: str, is_visible: bool = None, expand: List[str] = []) -> List[OfferInDB]:
        offers = await self.__offer_repository.select_all(
            section_id=section_id,
            is_visible=is_visible
        )

        if not expand or not offers:
            return offers

        return await self.__build_complete_offer(offers=offers, expand=expand)

    async def __build_complete_offer(self, offers: List[OfferInDB], expand: List[str]) -> List[CompleteOffer]:
        complete_offers = []

        for offer in offers:
            complete_offer_products = []

            for product in offer.products:
                file = None
                offer_product = CompleteOfferProduct(**product.model_dump())

                if "files" in expand:
                    if product.file_id:
                        file = await self.__file_repository.select_by_id(
                            id=product.file_id,
                            raise_404=False
                        )

                offer_product.file = file

                if product.sections:
                    complete_sections = []

                    for section in offer_product.sections:
                        complete_section = CompleteProductSection(**section.model_dump())
                        complete_items = []

                        for item in section.items:
                            complete_item = CompleteItem(**item.model_dump())

                            if item.file_id:
                                file_item = await self.__file_repository.select_by_id(
                                    id=item.file_id,
                                    raise_404=False
                                )
                                complete_item.file = file_item

                            complete_items.append(complete_item)

                        complete_section.items = complete_items
                        complete_sections.append(complete_section)

                    offer_product.sections = complete_sections

                complete_offer_products.append(offer_product)

            complete_offer = CompleteOffer.model_validate(offer)
            complete_offer.products = complete_offer_products
            complete_offers.append(complete_offer)

        return complete_offers

    async def delete_by_id(self, id: str) -> OfferInDB:
        offer_in_db = await self.__offer_repository.delete_by_id(id=id)
        return offer_in_db

    async def update_product_in_offers(self, product: ProductInDB) -> None:
        offers = await self.__offer_repository.select_all_by_product_id(
            product_id=product.id
        )

        for offer in offers:
            updated = False

            for offer_product in offer.products:
                if offer_product.product_id == product.id:
                    offer_product.name = product.name
                    offer_product.description = product.description
                    offer_product.unit_cost = product.unit_cost
                    offer_product.unit_price = product.unit_price
                    offer_product.file_id = product.file_id
                    offer_product.sections = product.sections
                    updated = True

            if updated:
                offer.unit_cost = sum(p.unit_cost for p in offer.products)
                offer.unit_price = sum(p.unit_price for p in offer.products)
                await self.__offer_repository.update(offer=offer)

    async def __create_offer_product(self, product_ids: List[str]) -> tuple[float, float, List[OfferProduct]]:
        total_cost = 0
        total_price = 0
        products = []

        for product_id in product_ids:
            product_in_db = await self.__product_repository.select_by_id(id=product_id)

            offer_product = OfferProduct(
                product_id=product_in_db.id,
                name=product_in_db.name,
                description=product_in_db.description,
                unit_cost=product_in_db.unit_cost,
                unit_price=product_in_db.unit_price,
                file_id=product_in_db.file_id,
                sections=product_in_db.sections
            )

            total_cost += offer_product.unit_cost
            total_price += offer_product.unit_price

            products.append(offer_product)

        return total_cost, total_price, products
