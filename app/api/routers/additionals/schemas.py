from typing import List
from pydantic import Field, ConfigDict
from app.api.shared_schemas.responses import Response
from app.crud.product_additionals.schemas import ProductAdditionalInDB
EXAMPLE_ADDITIONAL = {
    "id": "pad_123",
    "name": "Coberturas",
    "selection_type": "RADIO",
    "min_quantity": 0,
    "max_quantity": 1,
    "position": 1,
    "items": [
        {
            "position": 1,
            "product_id": "pro_123",
            "label": "Extra",
            "unit_price": 10,
            "unit_cost": 5,
            "consumption_factor": 1,
        }
    ],
    "organization_id": "org_123",
    "product_id": "pro_123",
}
class GetProductAdditionalResponse(Response):
    data: ProductAdditionalInDB | None = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "ProductAdditional found with success", "data": EXAMPLE_ADDITIONAL}})
class GetProductAdditionalsResponse(Response):
    data: List[ProductAdditionalInDB] = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "ProductAdditionals found with success", "data": [EXAMPLE_ADDITIONAL]}})
class CreateProductAdditionalResponse(Response):
    data: ProductAdditionalInDB | None = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "ProductAdditional created with success", "data": EXAMPLE_ADDITIONAL}})
class UpdateProductAdditionalResponse(Response):
    data: ProductAdditionalInDB | None = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "ProductAdditional updated with success", "data": EXAMPLE_ADDITIONAL}})
class DeleteProductAdditionalResponse(Response):
    data: ProductAdditionalInDB | None = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "ProductAdditional deleted with success", "data": EXAMPLE_ADDITIONAL}})
class AddAdditionalItemResponse(Response):
    data: ProductAdditionalInDB | None = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Item created with success", "data": EXAMPLE_ADDITIONAL}})
class UpdateAdditionalItemResponse(Response):
    data: ProductAdditionalInDB | None = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Item updated with success", "data": EXAMPLE_ADDITIONAL}})
class DeleteAdditionalItemResponse(Response):
    data: ProductAdditionalInDB | None = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Item deleted with success", "data": EXAMPLE_ADDITIONAL}})
