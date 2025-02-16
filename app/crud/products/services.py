from typing import List

from app.api.dependencies.get_plan_feature import get_plan_feature
from app.api.exceptions.authentication_exceptions import UnauthorizedException
from app.core.utils.features import Feature
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
        plan_feature = await get_plan_feature(
            organization_id=self.__product_repository.organization_id,
            feature_name=Feature.MAX_PRODUCTS
        )

        quantity = await self.__product_repository.select_count()

        if (quantity + 1) >= int(plan_feature.value):
            raise UnauthorizedException(detail=f"Maximum number of products reached, Max value: {plan_feature.value}")

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

    async def search_all(self, query: str, tags: List[str] = [], expand: List[str] = []) -> List[ProductInDB]:
        products = await self.__product_repository.select_all(
            query=query,
            tags=tags
        )

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
