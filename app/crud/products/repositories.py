from datetime import datetime
from typing import List
from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository

from .models import ProductModel
from .schemas import Product, ProductInDB

_logger = get_logger(__name__)


class ProductRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.organization_id = organization_id

    async def create(self, product: Product) -> ProductInDB:
        try:
            product_model = ProductModel(
                created_at=datetime.now(),
                updated_at=datetime.now(),
                organization_id=self.organization_id,
                **product.model_dump()
            )
            product_model.name = product_model.name.strip().title()

            product_model.save()
            _logger.info(f"Product {product.name} saved for organization {self.organization_id}")

            return ProductInDB.model_validate(product_model)

        except Exception as error:
            _logger.error(f"Error on create_product: {str(error)}")
            raise UnprocessableEntity(message="Error on create new product")

    async def update(self, product: ProductInDB) -> ProductInDB:
        try:
            product_model: ProductModel = ProductModel.objects(
                id=product.id,
                is_active=True,
                organization_id=self.organization_id
            ).first()
            product.name = product.name.strip().title()

            product_model.update(**product.model_dump())

            return await self.select_by_id(id=product.id)

        except Exception as error:
            _logger.error(f"Error on update_product: {str(error)}")
            raise UnprocessableEntity(message="Error on update product")

    async def select_count(self) -> int:
        try:
            count = ProductModel.objects(
                is_active=True,
                organization_id=self.organization_id,
            ).count()

            return count if count else 0

        except Exception as error:
            _logger.error(f"Error on select_count: {str(error)}")
            return 0

    async def select_by_id(self, id: str, raise_404: bool = True) -> ProductInDB:
        try:
            product_model: ProductModel = ProductModel.objects(
                id=id,
                is_active=True,
                organization_id=self.organization_id
            ).first()

            return ProductInDB.model_validate(product_model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            if raise_404:
                raise NotFoundError(message=f"Product #{id} not found")

    async def select_all(self, query: str, tags: List[str] = [], limit: int = None) -> List[ProductInDB]:
        try:
            products = []

            objects = ProductModel.objects(
                is_active=True,
                organization_id=self.organization_id
            )

            if query:
                objects = objects.filter(name__iregex=query)

            if tags:
                objects = objects.filter(tags__in=tags)

            if limit is not None:
                objects = objects.limit(limit)

            for product_model in objects.order_by("name"):
                products.append(ProductInDB.model_validate(product_model))

            return products

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"Products not found")

    async def delete_by_id(self, id: str) -> ProductInDB:
        try:
            product_model: ProductModel = ProductModel.objects(
                id=id,
                is_active=True,
                organization_id=self.organization_id
            ).first()

            if product_model:
                product_model.delete()

                return ProductInDB.model_validate(product_model)

            raise NotFoundError(message=f"Product #{id} not found")

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Product #{id} not found")
