from typing import List
from pydantic import Field, ConfigDict
from app.api.shared_schemas.responses import Response, ListResponseSchema
from app.crud.fast_orders.schemas import FastOrderInDB
EXAMPLE_FAST_ORDER = {
    "id": "fao_123",
    "products": [
        {
            "product_id": "prod_123",
            "name": "Brigadeiro",
            "unit_price": 1.5,
            "unit_cost": 0.75,
            "quantity": 2,
        }
    ],
    "order_date": "2024-01-01T00:00:00Z",
    "description": "Description",
    "additional": 2.5,
    "discount": 0,
    "organization_id": "org_123",
    "total_amount": 3.0,
    "payments": [],
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}
class GetFastOrderResponse(Response):
    data: FastOrderInDB | None = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Fast Order found with success", "data": EXAMPLE_FAST_ORDER}})
class GetFastOrdersResponse(ListResponseSchema):
    data: List[FastOrderInDB] = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Fast Orders found with success", "pagination": {"page": 1, "page_size": 1, "total": 1}, "data": [EXAMPLE_FAST_ORDER]}})
class CreateFastOrderResponse(Response):
    data: FastOrderInDB | None = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Fast Order created with success", "data": EXAMPLE_FAST_ORDER}})
class UpdateFastOrderResponse(Response):
    data: FastOrderInDB | None = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Fast Order updated with success", "data": EXAMPLE_FAST_ORDER}})
class DeleteFastOrderResponse(Response):
    data: FastOrderInDB | None = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Fast Order deleted with success", "data": EXAMPLE_FAST_ORDER}})
