from enum import Enum
from typing import List
from pydantic import Field
from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.crud.orders.schemas import Delivery
from app.crud.shared_schemas.payment import PaymentMethod


class PreOrderStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class PreOrderCustomer(GenericModel):
    customer_id: str | None = Field(default=None, example="cus_123")
    name: str = Field(example="Ted Mosby")
    ddd: str = Field(example="047")
    phone_number: str = Field(example="998899889")


class ProductAdditional(GenericModel):
    name: str = Field(example="Calabresa")
    quantity: int = Field(default=1, example=10, gt=0)


class SelectedOffer(GenericModel):
    offer_id: str = Field(example="off_123")
    quantity: int = Field(gt=0, example=1)
    additionals: List[ProductAdditional] | None = Field(default=[])


class PreOrderInDB(DatabaseModel):
    menu_id: str = Field(example="men_123")
    payment_method: PaymentMethod = Field(example=PaymentMethod.CASH)
    customer: PreOrderCustomer = Field(example={
        "name": "Ted Mosby",
        "ddd": "047",
        "phone_number": "998899889"
    })
    delivery: Delivery = Field(example={
        "delivery_type": "DELIVERY",
        "address": {
            "zip_code": "89066-000",
            "city": "Blumenau",
            "neighborhood": "Bairro dos testes",
            "line_1": "Rua de teste",
            "line_2": "Casa",
            "number": "123A",
        }
    })
    observation: str | None = Field(default=None, example="observation")
    offers: List[SelectedOffer] = Field(min_length=1, example=[
        {
            "offer_id": "off_123",
            "quantity": 5
        }
    ])
    status: PreOrderStatus | None = Field(default=PreOrderStatus.PENDING, example=PreOrderStatus.ACCEPTED)


class UpdatePreOrder(GenericModel):
    status: PreOrderStatus = Field()
