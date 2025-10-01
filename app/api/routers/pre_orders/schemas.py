from typing import List

from pydantic import ConfigDict, Field

from app.api.shared_schemas.responses import ListResponseSchema, Response
from app.api.routers.orders.schemas import EXAMPLE_ORDER
from app.crud.orders.schemas import OrderInDB
from app.crud.pre_orders.schemas import PreOrderInDB

EXAMPLE_PRE_ORDER = {
    "id": "pre_123",
    "organization_id": "org_123",
    "user_id": "usr_123",
    "code": "45623",
    "menu_id": "men_123",
    "payment_method": "CASH",
    "customer": {"name": "Ted Mosby", "ddd": "047", "phone_number": "998899889"},
    "delivery": {
        "delivery_type": "DELIVERY",
        "address": {
            "zip_code": "89066-000",
            "city": "Blumenau",
            "neighborhood": "Bairro dos testes",
            "line_1": "Rua de teste",
            "line_2": "Casa",
            "number": "123A",
        },
    },
    "observation": "observation",
    "offers": [
        {
            "offer_id": "off_123",
            "quantity": 1,
            "items": [
                {
                    "item_id": "item_1",
                    "section_id": "sec_1",
                    "name": "Bacon",
                    "file_id": None,
                    "unit_price": 5,
                    "unit_cost": 2,
                    "quantity": 1,
                    "additionals": [
                        {"additional_id": "pad_123", "item_id": "aitem_1", "quantity": 1}
                    ],
                }
            ],
        }
    ],
    "products": [
        {
            "product_id": "prod_123",
            "section_id": "sec_1",
            "name": "Brigadeiro",
            "file_id": None,
            "unit_price": 1.5,
            "unit_cost": 0.75,
            "quantity": 1,
            "additionals": [
                {"additional_id": "pad_123", "item_id": "aitem_1", "quantity": 1}
            ],
        }
    ],
    "status": "PENDING",
    "tax": 0,
    "total_amount": 123,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}


class PreOrderResponse(PreOrderInDB):
    """Response schema for a single pre-order."""

    model_config = ConfigDict(json_schema_extra={"example": EXAMPLE_PRE_ORDER})


class OrderResponse(OrderInDB):
    """Response schema for an order created from a pre-order."""

    model_config = ConfigDict(json_schema_extra={"example": EXAMPLE_ORDER})


class GetPreOrdersResponse(ListResponseSchema):
    data: List[PreOrderResponse] = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Pré pedidos encontrados com sucesso",
                "pagination": {"page": 1, "page_size": 1, "total": 1},
                "data": [EXAMPLE_PRE_ORDER],
            }
        }
    )


class GetPreOrderResponse(Response):
    data: PreOrderResponse | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Pré pedido encontrado com sucesso",
                "data": EXAMPLE_PRE_ORDER,
            }
        }
    )


class UpdatePreOrderResponse(Response):
    data: PreOrderResponse | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Pré pedido atualizado com sucesso",
                "data": EXAMPLE_PRE_ORDER,
            }
        }
    )


class DeletePreOrderResponse(Response):
    data: PreOrderResponse | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Pré pedido deletado com sucesso",
                "data": EXAMPLE_PRE_ORDER,
            }
        }
    )


class AcceptPreOrderResponse(Response):
    data: OrderResponse | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Pré pedido aceito com sucesso",
                "data": EXAMPLE_ORDER,
            }
        }
    )
