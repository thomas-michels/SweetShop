from datetime import datetime
from typing import List

from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository

from .models import ProductModel
from .schemas import Product, ProductInDB

_logger = get_logger(__name__)


class ProductRepository(Repository):
    def __init__(self) -> None:
        super().__init__()

    async def create(self, product: Product) -> ProductInDB:
        try:
            product_model = ProductModel(
                created_at=datetime.now(),
                updated_at=datetime.now(),
                **product.model_dump()
            )

            product_model.save()

            return ProductInDB.model_validate(product_model)

        except Exception as error:
            _logger.error(f"Error on create_product: {str(error)}")
            raise UnprocessableEntity(message="Error on create new product")

    async def update(self, product: ProductInDB) -> ProductInDB:
        try:
            product_model: ProductModel = ProductModel.objects(id=product_model.id, is_active=True).first()

            product_model.update(**product.model_dump())

            return ProductInDB.model_validate(product_model)

        except Exception as error:
            _logger.error(f"Error on update_product: {str(error)}")
            raise UnprocessableEntity(message="Error on update product")

    async def select_by_id(self, id: str) -> ProductInDB:
        try:
            product_model: ProductModel = ProductModel.objects(id=id, is_active=True).first()

            return ProductInDB.model_validate(product_model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            raise NotFoundError(message=f"Product #{id} not found")

    async def select_all(self) -> List[ProductInDB]:
        try:
            products = []

            for product_model in ProductModel.objects(is_active=True):
                products.append(ProductInDB.model_validate(product_model))

            return products

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"Products not found")

    async def delete_by_id(self, id: str) -> ProductInDB:
        try:
            product_model: ProductModel = ProductModel.objects(id=id, is_active=True).first()
            product_model.delete()

            return ProductInDB.model_validate(product_model)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Product #{id} not found")
