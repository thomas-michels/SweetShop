from typing import List

from app.crud.tags.repositories import TagRepository
from .schemas import CompleteProduct, Product, ProductInDB, UpdateProduct
from .repositories import ProductRepository


class ProductServices:

    def __init__(
            self,
            product_repository: ProductRepository,
            tag_repository: TagRepository,
        ) -> None:
        self.__product_repository = product_repository
        self.__tag_repository = tag_repository

    async def create(self, product: Product) -> ProductInDB:
        for tag in product.tags:
            await self.__tag_repository.select_by_id(id=tag)

        product_in_db = await self.__product_repository.create(product=product)
        return product_in_db

    async def update(self, id: str, updated_product: UpdateProduct) -> ProductInDB:
        product_in_db = await self.search_by_id(id=id)

        is_updated = product_in_db.validate_updated_fields(update_product=updated_product)

        if is_updated:
            if updated_product.tags is not None:
                for tag in updated_product.tags:
                    await self.__tag_repository.select_by_id(id=tag)

            product_in_db = await self.__product_repository.update(product=product_in_db)

        return product_in_db

    async def search_by_id(self, id: str) -> ProductInDB:
        product_in_db = await self.__product_repository.select_by_id(id=id)
        return product_in_db

    async def search_all(self, query: str, expand: List[str] = []) -> List[ProductInDB]:
        products = await self.__product_repository.select_all(query=query)

        if not expand:
            return products

        complete_products = []
        tags = {}

        for product in products:
            complete_product = CompleteProduct(**product.model_dump())

            if "tags" in expand:
                complete_product.tags = []

                for tag in product.tags:
                    if tags.get(tag):
                        tag_in_db = tags[tag]

                    else:
                        tag_in_db = await self.__tag_repository.select_by_id(
                            id=tag,
                            raise_404=False
                        )
                        if tag_in_db:
                            tags[tag_in_db.id] = tag_in_db

                    complete_product.tags.append(tag_in_db)

            complete_products.append(complete_product)

        return complete_products

    async def delete_by_id(self, id: str) -> ProductInDB:
        product_in_db = await self.__product_repository.delete_by_id(id=id)
        return product_in_db
