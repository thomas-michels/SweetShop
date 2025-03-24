from typing import List
from app.api.dependencies.bucket import S3BucketManager
from app.api.dependencies.get_plan_feature import get_plan_feature
from app.api.exceptions.authentication_exceptions import UnauthorizedException, BadRequestException
from app.core.utils.features import Feature
from app.crud.files.schemas import FilePurpose
from app.crud.tags.repositories import TagRepository
from app.crud.files.repositories import FileRepository
from .schemas import CompleteProduct, Product, ProductInDB, UpdateProduct
from .repositories import ProductRepository


class ProductServices:

    def __init__(
            self,
            product_repository: ProductRepository,
            tag_repository: TagRepository,
            file_repository: FileRepository,
        ) -> None:
        self.__product_repository = product_repository
        self.__tag_repository = tag_repository
        self.__file_repository = file_repository
        self.__s3_manager = S3BucketManager(mode="private")

    async def create(self, product: Product) -> ProductInDB:
        plan_feature = await get_plan_feature(
            organization_id=self.__product_repository.organization_id,
            feature_name=Feature.MAX_PRODUCTS
        )

        quantity = await self.__product_repository.select_count()

        if not plan_feature or (quantity + 1) >= int(plan_feature.value):
            raise UnauthorizedException(detail=f"Maximum number of products reached, Max value: {plan_feature.value}")

        if product.file_id:
            file_in_db = await self.__file_repository.select_by_id(id=product.file_id)

            if file_in_db.purpose != FilePurpose.PRODUCT:
                raise BadRequestException(detail="Invalid image for the product")

        for tag in product.tags:
            await self.__tag_repository.select_by_id(id=tag)

        product_in_db = await self.__product_repository.create(product=product)
        return product_in_db

    async def update(self, id: str, updated_product: UpdateProduct) -> ProductInDB:
        product_in_db = await self.search_by_id(id=id)

        if updated_product.file_id is not None:
            file_in_db = await self.__file_repository.select_by_id(id=updated_product.file_id)

            if file_in_db.purpose != FilePurpose.PRODUCT:
                raise BadRequestException(detail="Invalid image for the product")

            if product_in_db.file_id:
                old_file = await self.__file_repository.delete_by_id(id=product_in_db.file_id)

                self.__s3_manager.delete_file_by_url(file_url=old_file.url)

        is_updated = product_in_db.validate_updated_fields(update_product=updated_product)

        if is_updated:
            if updated_product.tags is not None:
                for tag in updated_product.tags:
                    await self.__tag_repository.select_by_id(id=tag)

            product_in_db = await self.__product_repository.update(product=product_in_db)

        return product_in_db

    async def search_count(self) -> int:
        return await self.__product_repository.select_count()

    async def search_by_id(self, id: str, expand: List[str] = []) -> ProductInDB:
        product_in_db = await self.__product_repository.select_by_id(id=id)

        if not expand or not product_in_db:
            return product_in_db

        complete_product = await self.__build_complete_product(products=[product_in_db], expand=expand)
        return complete_product[0]

    async def search_all(self, query: str, tags: List[str] = [], expand: List[str] = []) -> List[ProductInDB]:
        products = await self.__product_repository.select_all(
            query=query,
            tags=tags
        )

        if not expand:
            return products

        return await self.__build_complete_product(products=products, expand=expand)

    async def __build_complete_product(self, products: List[ProductInDB], expand: List[str]) -> List[CompleteProduct]:
        complete_products = []
        tags = {}

        for product in products:
            complete_product = CompleteProduct(**product.model_dump())

            if "file" in expand:
                complete_product.file = await self.__file_repository.select_by_id(
                    id=complete_product.file_id,
                    raise_404=False
                )

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
