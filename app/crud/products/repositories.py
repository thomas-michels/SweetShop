from datetime import datetime
from typing import List
from mongoengine.errors import NotUniqueError
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
            product_model.name = product_model.name.capitalize()

            product_model.save()
            _logger.info(f"Product {product.name} saved for organization {self.organization_id}")

            return ProductInDB.model_validate(product_model)

        except NotUniqueError:
            _logger.warning(f"Product with name {product.name} is not unique")
            return await self.select_by_name(name=product.name)

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
            product.name = product.name.capitalize()

            product_model.update(**product.model_dump())

            return ProductInDB.model_validate(product_model)

        except Exception as error:
            _logger.error(f"Error on update_product: {str(error)}")
            raise UnprocessableEntity(message="Error on update product")

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

    async def select_by_name(self, name: str) -> ProductInDB:
        try:
            name = name.capitalize()
            product_model: ProductModel = ProductModel.objects(
                name=name,
                is_active=True,
                organization_id=self.organization_id
            ).first()

            return ProductInDB.model_validate(product_model)

        except Exception as error:
            _logger.error(f"Error on select_by_name: {str(error)}")
            raise NotFoundError(message=f"Product with name {name} not found")

    async def select_all(self, query: str) -> List[ProductInDB]:
        try:
            products = []

            if query:
                objects = ProductModel.objects(
                    is_active=True,
                    name__iregex=query,
                    organization_id=self.organization_id
                )

            else:
                objects = ProductModel.objects(
                    is_active=True,
                    organization_id=self.organization_id
                )

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
            product_model.delete()

            return ProductInDB.model_validate(product_model)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Product #{id} not found")
