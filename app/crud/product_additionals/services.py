from typing import List

from app.crud.products.repositories import ProductRepository
from app.crud.additional_items.repositories import AdditionalItemRepository
from app.crud.additional_items.schemas import AdditionalItem, CompleteAdditionalItem
from app.crud.files.repositories import FileRepository

from .repositories import ProductAdditionalRepository
from .schemas import (
    ProductAdditional,
    ProductAdditionalInDB,
    UpdateProductAdditional,
)


class ProductAdditionalServices:
    def __init__(
        self,
        additional_repository: ProductAdditionalRepository,
        product_repository: ProductRepository,
        item_repository: AdditionalItemRepository,
        file_repository: FileRepository,
    ) -> None:
        self.__repository = additional_repository
        self.__product_repository = product_repository
        self.__item_repository = item_repository
        self.__file_repository = file_repository

    async def create(self, product_additional: ProductAdditional, product_id: str) -> ProductAdditionalInDB:
        await self.__product_repository.select_by_id(id=product_id)

        for item in product_additional.items:
            if item.product_id:
                await self.__product_repository.select_by_id(id=item.product_id)
            if item.file_id:
                await self.__file_repository.select_by_id(id=item.file_id)

        additional_in_db = await self.__repository.create(
            product_additional=product_additional,
            product_id=product_id
        )

        for item in product_additional.items:
            await self.__item_repository.create(additional_id=additional_in_db.id, item=item)

        additional_in_db.items = await self.__item_repository.select_all(additional_id=additional_in_db.id)
        return additional_in_db

    async def update(self, id: str, updated_product_additional: UpdateProductAdditional) -> ProductAdditionalInDB:
        additional_in_db = await self.search_by_id(id=id)

        is_updated = additional_in_db.validate_updated_fields(update=updated_product_additional)

        if is_updated:
            if updated_product_additional.items is not None:
                for item in updated_product_additional.items:
                    if item.product_id:
                        await self.__product_repository.select_by_id(id=item.product_id)
                    if item.file_id:
                        await self.__file_repository.select_by_id(id=item.file_id)

            additional_in_db = await self.__repository.update(product_additional=additional_in_db)

        additional_in_db.items = await self.__item_repository.select_all(additional_id=id)
        return additional_in_db

    async def search_by_id(self, id: str) -> ProductAdditionalInDB:
        additional = await self.__repository.select_by_id(id=id)

        if additional:
            items = await self.__item_repository.select_all(additional_id=id)
            additional.items = await self.__build_complete_items(items)

        return additional

    async def search_all(self) -> List[ProductAdditionalInDB]:
        additionals = await self.__repository.select_all()
        for additional in additionals:
            items = await self.__item_repository.select_all(additional_id=additional.id)
            additional.items = await self.__build_complete_items(items)

        return additionals

    async def search_by_product_id(self, product_id: str) -> List[ProductAdditionalInDB]:
        additionals = await self.__repository.select_by_product_id(product_id=product_id)

        for additional in additionals:
            items = await self.__item_repository.select_all(additional_id=additional.id)
            additional.items = await self.__build_complete_items(items)

        return additionals

    async def delete_by_id(self, id: str) -> ProductAdditionalInDB:
        return await self.__repository.delete_by_id(id=id)

    async def add_item(self, additional_id: str, item: AdditionalItem) -> ProductAdditionalInDB:
        if item.product_id:
            await self.__product_repository.select_by_id(id=item.product_id)
        if item.file_id:
            await self.__file_repository.select_by_id(id=item.file_id)

        await self.__item_repository.create(additional_id=additional_id, item=item)

        return await self.search_by_id(id=additional_id)

    async def update_item(
        self, additional_id: str, item_id: str, item: AdditionalItem
    ) -> ProductAdditionalInDB:
        if item.product_id:
            await self.__product_repository.select_by_id(id=item.product_id)
        if item.file_id:
            await self.__file_repository.select_by_id(id=item.file_id)

        existing = await self.__item_repository.select_by_id(id=item_id)

        existing.position = item.position
        existing.product_id = item.product_id
        existing.label = item.label
        existing.unit_price = item.unit_price
        existing.unit_cost = item.unit_cost
        existing.consumption_factor = item.consumption_factor
        existing.file_id = item.file_id

        await self.__item_repository.update(item=existing)
        return await self.search_by_id(id=additional_id)

    async def delete_item(self, additional_id: str, item_id: str) -> ProductAdditionalInDB:
        await self.__item_repository.delete_by_id(id=item_id)
        return await self.search_by_id(id=additional_id)

    async def delete_by_product_id(self, product_id: str) -> None:
        additionals = await self.__repository.select_by_product_id(product_id=product_id)
        for additional in additionals:
            await self.__item_repository.delete_by_additional_id(additional_id=additional.id)
            await self.__repository.delete_by_id(id=additional.id)

    async def __build_complete_items(self, items: List[AdditionalItem]) -> List[AdditionalItem]:
        complete_items: List[CompleteAdditionalItem] = []

        for item in items:
            complete = CompleteAdditionalItem(**item.model_dump())
            if item.file_id:
                complete.file = await self.__file_repository.select_by_id(
                    id=item.file_id,
                    raise_404=False,
                )
            complete_items.append(complete)

        return complete_items
