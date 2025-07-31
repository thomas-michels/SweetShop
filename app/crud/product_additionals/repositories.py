from typing import List

from pydantic import ValidationError

from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository
from app.core.utils.utc_datetime import UTCDateTime

from .models import ProductAdditionalModel
from .schemas import ProductAdditional, ProductAdditionalInDB

_logger = get_logger(__name__)


class ProductAdditionalRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.organization_id = organization_id

    def _to_schema(self, model: ProductAdditionalModel) -> ProductAdditionalInDB:
        data = model.to_mongo().to_dict()
        data["id"] = str(model.id)
        data["created_at"] = model.created_at
        data["updated_at"] = model.updated_at
        # items are stored in a separate collection
        data["items"] = {}
        return ProductAdditionalInDB.model_validate(data)

    async def create(self, product_additional: ProductAdditional) -> ProductAdditionalInDB:
        try:
            data = product_additional.model_dump()
            # items are handled by AdditionalItemRepository
            data.pop("items", None)

            model = ProductAdditionalModel(
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
                organization_id=self.organization_id,
                **data,
            )
            model.save()
            return self._to_schema(model)
        except Exception as error:
            _logger.error(f"Error on create_product_additional: {error}")
            raise UnprocessableEntity(message="Error on create new product additional")

    async def update(self, product_additional: ProductAdditionalInDB) -> ProductAdditionalInDB:
        try:
            model: ProductAdditionalModel = ProductAdditionalModel.objects(
                id=product_additional.id, is_active=True, organization_id=self.organization_id
            ).first()

            data = product_additional.model_dump()
            data.pop("items", None)

            for field in ["id", "organization_id", "created_at", "_id"]:
                data.pop(field, None)

            data["updated_at"] = product_additional.updated_at

            model.update(**data)

            return await self.select_by_id(id=product_additional.id)
        except ValidationError:
            raise NotFoundError(message="ProductAdditional not found")
        except Exception as error:
            _logger.error(f"Error on update_product_additional: {error}")
            raise UnprocessableEntity(message="Error on update product additional")

    async def select_by_id(self, id: str, raise_404: bool = True) -> ProductAdditionalInDB:
        try:
            model: ProductAdditionalModel = ProductAdditionalModel.objects(
                id=id, is_active=True, organization_id=self.organization_id
            ).first()
            return self._to_schema(model)
        except ValidationError:
            if raise_404:
                raise NotFoundError(message=f"ProductAdditional #{id} not found")
        except Exception as error:
            _logger.error(f"Error on select_by_id: {error}")
            if raise_404:
                raise NotFoundError(message=f"ProductAdditional #{id} not found")

    async def select_all(self) -> List[ProductAdditionalInDB]:
        try:
            results = []
            objects = ProductAdditionalModel.objects(
                is_active=True,
                organization_id=self.organization_id,
            ).order_by("position")
            for model in objects:
                results.append(self._to_schema(model))
            return results
        except Exception as error:
            _logger.error(f"Error on select_all: {error}")
            raise NotFoundError(message="Product additionals not found")

    async def delete_by_id(self, id: str) -> ProductAdditionalInDB:
        try:
            model: ProductAdditionalModel = ProductAdditionalModel.objects(
                id=id, is_active=True, organization_id=self.organization_id
            ).first()
            if model:
                model.delete()
                return self._to_schema(model)
            raise NotFoundError(message=f"ProductAdditional #{id} not found")
        except Exception as error:
            _logger.error(f"Error on delete_by_id: {error}")
            raise NotFoundError(message=f"ProductAdditional #{id} not found")
