from typing import List

from pydantic import Field, ConfigDict

from app.api.shared_schemas.responses import Response, ListResponseSchema
from app.crud.orders.schemas import OrderInDB

EXAMPLE_ORDER = {
    "id": "ord_123",
    "customer_id": "cus_123",
    "status": "PENDING",
    "products": [
        {
            "product_id": "pro_123",
            "name": "Brigadeiro",
            "unit_price": 1.5,
            "unit_cost": 0.75,
            "quantity": 1,
            "additionals": [],
        }
    ],
    "tags": [],
    "delivery": {
        "delivery_type": "WITHDRAWAL",
        "delivery_at": None,
        "delivery_value": None,
        "address": None,
    },
    "preparation_date": "2024-01-01T00:00:00Z",
    "order_date": "2024-01-01T00:00:00Z",
    "description": "Description",
    "additional": 0,
    "discount": 0,
    "reason_id": None,
    "tax": 0,
    "organization_id": "org_123",
    "total_amount": 10.0,
    "payments": [],
    "payment_status": "PENDING",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}


class GetOrderByIdResponse(Response):
    data: OrderInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Order found with success",
                "data": EXAMPLE_ORDER,
            }
        }
    )


class GetOrdersResponse(ListResponseSchema):
    data: List[OrderInDB] = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Orders found with success",
                "pagination": {"page": 1, "page_size": 2, "total": 2},
                "data": [
                    EXAMPLE_ORDER,
                    {**EXAMPLE_ORDER, "id": "ord_456"},
                ],
            }
        }
    )


class CreateOrderResponse(Response):
    data: OrderInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Order created with success",
                "data": EXAMPLE_ORDER,
            }
        }
    )


class UpdateOrderResponse(Response):
    data: OrderInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Order updated with success",
                "data": EXAMPLE_ORDER,
            }
        }
    )


class DeleteOrderResponse(Response):
    data: OrderInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Order deleted with success",
                "data": EXAMPLE_ORDER,
            }
        }
    )
