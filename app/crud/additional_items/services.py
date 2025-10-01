from typing import List

from app.crud.product_additionals.repositories import ProductAdditionalRepository

from .repositories import AdditionalItemRepository
from .schemas import AdditionalItem, AdditionalItemInDB, UpdateAdditionalItem


class AdditionalItemServices:
    def __init__(
        self,
        item_repository: AdditionalItemRepository,
        additional_repository: ProductAdditionalRepository,
    ) -> None:
        self.__item_repository = item_repository
        self.__additional_repository = additional_repository

    async def create(self, additional_id: str, item: AdditionalItem) -> AdditionalItemInDB:
        await self.__additional_repository.select_by_id(id=additional_id)
        return await self.__item_repository.create(additional_id=additional_id, item=item)

    async def update(self, id: str, updated_item: UpdateAdditionalItem) -> AdditionalItemInDB:
        item_in_db = await self.search_by_id(id=id)
        is_updated = item_in_db.validate_updated_fields(update=updated_item)
        if is_updated:
            item_in_db = await self.__item_repository.update(item=item_in_db)
        return item_in_db

    async def search_by_id(self, id: str) -> AdditionalItemInDB:
        return await self.__item_repository.select_by_id(id=id)

    async def search_all(self, additional_id: str) -> List[AdditionalItemInDB]:
        return await self.__item_repository.select_all(additional_id=additional_id)

    async def delete_by_id(self, id: str) -> AdditionalItemInDB:
        return await self.__item_repository.delete_by_id(id=id)
