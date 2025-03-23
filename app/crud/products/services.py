import os
from typing import List
from uuid import uuid4

from fastapi import UploadFile
from tempfile import NamedTemporaryFile
from app.api.dependencies.bucket import S3BucketManager
from app.api.dependencies.get_plan_feature import get_plan_feature
from app.api.exceptions.authentication_exceptions import UnauthorizedException
from app.core.utils.features import Feature
from app.core.utils.image_validator import validate_image_file
from app.core.utils.resize_image import resize_image
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
        self.__s3_manager = S3BucketManager(mode="private")

    async def create(self, product: Product) -> ProductInDB:
        plan_feature = await get_plan_feature(
            organization_id=self.__product_repository.organization_id,
            feature_name=Feature.MAX_PRODUCTS
        )

        quantity = await self.__product_repository.select_count()

        if not plan_feature or (quantity + 1) >= int(plan_feature.value):
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

    async def add_image(self, product_id: str, product_image: UploadFile) -> ProductInDB:
        product_in_db = await self.search_by_id(id=product_id)

        image_type = await validate_image_file(image=product_image)

        image_id = str(uuid4())

        product_image = await resize_image(
            upload_image=product_image,
            size=(400, 400)
        )

        image_extension = product_image.filename.split(".")[-1]  # Obtém a extensão original

        with NamedTemporaryFile(mode="wb", suffix=f".{image_extension}", delete=False) as buffer:
            buffer.write(await product_image.read())
            buffer.flush()

        image_url = self.__s3_manager.upload_file(
            local_path=buffer.name,
            bucket_path=f"organization/{product_in_db.organization_id}/products/{product_in_db.id}_{image_id}.{image_extension}"
        )

        os.remove(buffer.name)

        if product_in_db.image_url:
            self.__s3_manager.delete_file_by_url(file_url=product_in_db.image_url)

        product_in_db.image_url = image_url
        product_in_db = await self.__product_repository.update(product=product_in_db)

        return product_in_db

    async def search_count(self) -> int:
        return await self.__product_repository.select_count()

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
