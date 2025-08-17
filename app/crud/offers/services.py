from typing import List

from app.api.exceptions.authentication_exceptions import BadRequestException
from app.crud.files.repositories import FileRepository
from app.crud.files.schemas import FilePurpose, FileInDB
from app.crud.products.repositories import ProductRepository
from app.crud.products.schemas import ProductInDB
from app.crud.section_items.repositories import SectionItemRepository
from app.crud.section_items.schemas import ItemType

from .repositories import OfferRepository
from .schemas import (
    CompleteOffer,
    CompleteOfferProduct,
    OfferProduct,
    OfferProductRequest,
    RequestOffer,
    Offer,
    OfferInDB,
    UpdateOffer,
)


class OfferServices:

    def __init__(
        self,
        offer_repository: OfferRepository,
        product_repository: ProductRepository,
        file_repository: FileRepository,
        section_item_repository: SectionItemRepository,
    ) -> None:
        self.__offer_repository = offer_repository
        self.__product_repository = product_repository
        self.__file_repository = file_repository
        self.__section_item_repository = section_item_repository

    async def create(self, request_offer: RequestOffer) -> OfferInDB:
        total_cost, total_price, products = await self.__create_offer_product(
            product_items=request_offer.products
        )

        if request_offer.file_id is not None:
            file_in_db = await self.__file_repository.select_by_id(id=request_offer.file_id)
            if file_in_db.purpose != FilePurpose.OFFER:
                raise BadRequestException(detail="Invalid image for the offer")

        offer = Offer(
            name=request_offer.name,
            description=request_offer.description,
            file_id=request_offer.file_id,
            unit_price=(
                request_offer.unit_price
                if request_offer.unit_price is not None
                else total_price
            ),
            unit_cost=total_cost,
            products=products,
            starts_at=request_offer.starts_at,
            ends_at=request_offer.ends_at,
            is_visible=request_offer.is_visible,
        )

        offer_in_db = await self.__offer_repository.create(offer=offer)

        return offer_in_db

    async def update(self, id: str, updated_offer: UpdateOffer) -> OfferInDB:
        offer_in_db = await self.search_by_id(id=id)

        is_updated = offer_in_db.validate_updated_fields(update_offer=updated_offer)

        if is_updated:
            if updated_offer.products is not None:
                product_cost, product_price, products = await self.__create_offer_product(
                    product_items=updated_offer.products
                )
                offer_in_db.products = products
            else:
                product_cost = sum(p.unit_cost * p.quantity for p in offer_in_db.products)
                product_price = sum(p.unit_price * p.quantity for p in offer_in_db.products)

            offer_in_db.unit_cost = product_cost

            if updated_offer.unit_price is not None:
                offer_in_db.unit_price = updated_offer.unit_price
            else:
                offer_in_db.unit_price = product_price

            if updated_offer.file_id is not None:
                file_in_db = await self.__file_repository.select_by_id(id=updated_offer.file_id)
                if file_in_db.purpose != FilePurpose.OFFER:
                    raise BadRequestException(detail="Invalid image for the offer")
                offer_in_db.file_id = updated_offer.file_id

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

    async def search_all_paginated(
        self,
        query: str = None,
        expand: List[str] = [],
        page: int = None,
        page_size: int = None,
        is_visible: bool = None,
    ) -> List[OfferInDB]:
        offers = await self.__offer_repository.select_all_paginated(
            query=query,
            page=page,
            page_size=page_size,
            is_visible=is_visible,
        )

        if not expand:
            return offers

        return await self.__build_complete_offer(offers=offers, expand=expand)

    async def search_count(self, query: str = None, is_visible: bool = None) -> int:
        return await self.__offer_repository.select_count(query=query, is_visible=is_visible)

    async def __build_complete_offer(self, offers: List[OfferInDB], expand: List[str]) -> List[CompleteOffer]:
        complete_offers = []

        files_map: dict[str, FileInDB] = {}

        if "files" in expand:
            file_ids = set()
            for offer in offers:
                if offer.file_id:
                    file_ids.add(offer.file_id)
                for product in offer.products:
                    if product.file_id:
                        file_ids.add(product.file_id)

            files_map = await self.__file_repository.select_by_ids(list(file_ids))

        for offer in offers:
            complete_offer_products = []

            for product in offer.products:
                offer_product = CompleteOfferProduct(**product.model_dump())

                if "files" in expand and product.file_id:
                    offer_product.file = files_map.get(product.file_id)

                complete_offer_products.append(offer_product)

            complete_offer = CompleteOffer.model_validate(offer)
            complete_offer.products = complete_offer_products

            if "files" in expand and offer.file_id:
                complete_offer.file = files_map.get(offer.file_id)

            complete_offers.append(complete_offer)

        return complete_offers

    async def delete_by_id(self, id: str) -> OfferInDB:
        offer_in_db = await self.__offer_repository.delete_by_id(id=id)
        await self.__section_item_repository.delete_by_item_id(item_id=id, item_type=ItemType.OFFER)
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
                    updated = True

            if updated:
                product_cost = sum(p.unit_cost * p.quantity for p in offer.products)
                product_price = sum(p.unit_price * p.quantity for p in offer.products)
                offer.unit_cost = product_cost
                offer.unit_price = product_price
                await self.__offer_repository.update(offer=offer)

    async def __create_offer_product(self, product_items: List[OfferProductRequest]) -> tuple[float, float, List[OfferProduct]]:
        total_cost = 0
        total_price = 0
        products = []

        for product_item in product_items:
            product_in_db = await self.__product_repository.select_by_id(id=product_item.product_id)

            offer_product = OfferProduct(
                product_id=product_in_db.id,
                name=product_in_db.name,
                description=product_in_db.description,
                unit_cost=product_in_db.unit_cost,
                unit_price=product_in_db.unit_price,
                quantity=product_item.quantity,
                file_id=product_in_db.file_id,
            )

            total_cost += offer_product.unit_cost * offer_product.quantity
            total_price += offer_product.unit_price * offer_product.quantity

            products.append(offer_product)

        return total_cost, total_price, products

