from typing import List

from app.crud.products.repositories import ProductRepository
from app.crud.additional_items.repositories import AdditionalItemRepository

from .repositories import ProductAdditionalRepository
from .schemas import (
    ProductAdditional,
    ProductAdditionalInDB,
    UpdateProductAdditional,
    AdditionalItem,
)


class ProductAdditionalServices:
    def __init__(
        self,
        additional_repository: ProductAdditionalRepository,
        product_repository: ProductRepository,
        item_repository: AdditionalItemRepository,
    ) -> None:
        self.__repository = additional_repository
        self.__product_repository = product_repository
        self.__item_repository = item_repository

    async def create(self, product_additional: ProductAdditional) -> ProductAdditionalInDB:
        for item in product_additional.items.values():
            if item.product_id:
                await self.__product_repository.select_by_id(id=item.product_id)

        additional_in_db = await self.__repository.create(product_additional=product_additional)

        for item in product_additional.items.values():
            await self.__item_repository.create(additional_id=additional_in_db.id, item=item)

        additional_in_db.items = {
            itm.position: itm for itm in await self.__item_repository.select_all(additional_id=additional_in_db.id)
        }
        return additional_in_db

    async def update(self, id: str, updated_product_additional: UpdateProductAdditional) -> ProductAdditionalInDB:
        additional_in_db = await self.search_by_id(id=id)

        is_updated = additional_in_db.validate_updated_fields(update=updated_product_additional)

        if is_updated:
            if updated_product_additional.items is not None:
                for item in updated_product_additional.items.values():
                    if item.product_id:
                        await self.__product_repository.select_by_id(id=item.product_id)
            additional_in_db = await self.__repository.update(product_additional=additional_in_db)

        additional_in_db.items = {
            itm.position: itm for itm in await self.__item_repository.select_all(additional_id=id)
        }
        return additional_in_db

    async def search_by_id(self, id: str) -> ProductAdditionalInDB:
        additional = await self.__repository.select_by_id(id=id)
        if additional:
            items = await self.__item_repository.select_all(additional_id=id)
            additional.items = {itm.position: itm for itm in items}
        return additional

    async def search_all(self) -> List[ProductAdditionalInDB]:
        additionals = await self.__repository.select_all()
        for additional in additionals:
            items = await self.__item_repository.select_all(additional_id=additional.id)
            additional.items = {itm.position: itm for itm in items}
        return additionals

    async def search_by_product_id(
        self, product_id: str, additionals: List[ProductAdditional | dict] | None = None
    ) -> List[ProductAdditionalInDB | ProductAdditional]:
        if additionals is None:
            product = await self.__product_repository.select_by_id(id=product_id)
            additionals = product.additionals
        ids = []
        plain: List[ProductAdditional | dict] = []
        for additional in additionals:
            additional_id = getattr(additional, "id", None)
            if additional_id is None and isinstance(additional, dict):
                additional_id = additional.get("id")
            if additional_id:
                ids.append(additional_id)
            else:
                plain.append(additional)
        result: List[ProductAdditionalInDB | ProductAdditional] = []
        if ids:
            additionals = await self.__repository.select_by_ids(ids=ids)
            items_map = await self.__item_repository.select_all_for_additionals(additional_ids=ids)
            for additional in additionals:
                additional.items = {itm.position: itm for itm in items_map.get(additional.id, [])}
            result.extend(additionals)
        result.extend(plain)
        return result

    async def delete_by_id(self, id: str) -> ProductAdditionalInDB:
        return await self.__repository.delete_by_id(id=id)

    async def add_item(self, additional_id: str, item: AdditionalItem) -> ProductAdditionalInDB:
        if item.product_id:
            await self.__product_repository.select_by_id(id=item.product_id)
        await self.__item_repository.create(additional_id=additional_id, item=item)
        return await self.search_by_id(id=additional_id)

    async def update_item(
        self, additional_id: str, item_id: str, item: AdditionalItem
    ) -> ProductAdditionalInDB:
        if item.product_id:
            await self.__product_repository.select_by_id(id=item.product_id)
        existing = await self.__item_repository.select_by_id(id=item_id)
        existing.position = item.position
        existing.product_id = item.product_id
        existing.label = item.label
        existing.unit_price = item.unit_price
        existing.unit_cost = item.unit_cost
        existing.consumption_factor = item.consumption_factor
        await self.__item_repository.update(item=existing)
        return await self.search_by_id(id=additional_id)

    async def delete_item(self, additional_id: str, item_id: str) -> ProductAdditionalInDB:
        await self.__item_repository.delete_by_id(id=item_id)
        return await self.search_by_id(id=additional_id)
