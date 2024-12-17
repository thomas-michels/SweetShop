from typing import List
from .schemas import Product, ProductInDB, UpdateProduct
from .repositories import ProductRepository


class ProductServices:

    def __init__(self, product_repository: ProductRepository) -> None:
        self.__repository = product_repository

    async def create(self, product: Product) -> ProductInDB:
        product_in_db = await self.__repository.create(product=product)
        return product_in_db

    async def update(self, id: str, updated_product: UpdateProduct) -> ProductInDB:
        product_in_db = await self.search_by_id(id=id)

        is_updated = product_in_db.validate_updated_fields(update_product=updated_product)

        if is_updated:
            product_in_db = await self.__repository.update(product=product_in_db)

        return product_in_db

    async def search_by_id(self, id: str) -> ProductInDB:
        product_in_db = await self.__repository.select_by_id(id=id)
        return product_in_db

    async def search_all(self, query: str) -> List[ProductInDB]:
        products = await self.__repository.select_all(query=query)
        return products

    async def delete_by_id(self, id: str) -> ProductInDB:
        product_in_db = await self.__repository.delete_by_id(id=id)
        return product_in_db
