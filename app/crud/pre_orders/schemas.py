from enum import Enum
from typing import List, Literal, Union
from pydantic import Field, model_validator
from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.core.utils.utc_datetime import UTCDateTime, UTCDateTimeType
from app.crud.shared_schemas.address import Address
from app.crud.shared_schemas.payment import PaymentMethod


class PreOrderStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class PreOrderCustomer(GenericModel):
    customer_id: str | None = Field(default=None, example="cus_123")
    name: str = Field(example="Ted Mosby")
    international_code: str | None = Field(default=None, example="55")
    ddd: str = Field(example="047")
    phone_number: str = Field(example="998899889")

    @model_validator(mode="after")
    def model_validate(self) -> "PreOrderCustomer":
        if self.international_code is None:
            self.international_code = "55"

        return self


class DeliveryType(str, Enum):
    FAST_ORDER = "FAST_ORDER"
    WITHDRAWAL = "WITHDRAWAL"
    DELIVERY = "DELIVERY"


class Delivery(GenericModel):
    delivery_type: DeliveryType = Field(
        default=DeliveryType.WITHDRAWAL, example=DeliveryType.WITHDRAWAL
    )
    delivery_at: UTCDateTimeType | None = Field(default=None, example=str(UTCDateTime.now()))
    delivery_value: float | None = Field(default=None)
    address: Address | None = Field(default=None)

    @model_validator(mode="after")
    def validate_model(self) -> "Delivery":
        if self.delivery_type == DeliveryType.DELIVERY:
            if self.address is None:
                raise ValueError("`address` must be set for DELIVERY type")

            if self.delivery_value is None:
                raise ValueError("`delivery_value` must be set for DELIVERY type")

            if self.delivery_at is None:
                raise ValueError("`delivery_at` must be set for DELIVERY type")

        else:
            if self.delivery_at or self.address or self.delivery_value:
                raise ValueError(
                    "`delivery_at`, `address`, and `delivery_value` must be None when type is WITHDRAWAL"
                )

        return self


class SelectedAdditional(GenericModel):
    additional_id: str = Field(example="pad_123")
    item_id: str = Field(example="aitem_123")
    name: str | None = Field(default=None, example="Bacon extra")
    unit_price: float = Field(ge=0, example=1.5)
    quantity: int = Field(ge=1, example=1)


class SelectedOfferItem(GenericModel):
    item_id: str = Field(example="123")
    section_id: str = Field(example="123")
    name: str = Field(example="Bacon")
    file_id: str | None = Field(default=None)
    unit_price: float = Field(ge=0)
    unit_cost: float = Field(ge=0)
    quantity: int = Field(ge=1, example=1)
    additionals: List[SelectedAdditional] = Field(default=[])


class SelectedBase(GenericModel):
    quantity: int = Field(ge=1, example=1)
    observation: str | None = Field(
        default=None,
        example="Sem cebola / aniversário 20h",
    )


class SelectedProduct(SelectedBase):
    kind: Literal["PRODUCT"] = "PRODUCT"
    product_id: str = Field(example="prod_123")
    section_id: str = Field(example="123")
    name: str = Field(example="Brigadeiro")
    file_id: str | None = Field(default=None)
    unit_price: float = Field(ge=0)
    unit_cost: float = Field(ge=0)
    additionals: List[SelectedAdditional] = Field(default=[])


class SelectedOffer(SelectedBase):
    kind: Literal["OFFER"] = "OFFER"
    offer_id: str = Field(example="off_123")
    name: str = Field(example="Combo")
    description: str | None = Field(default=None)
    file_id: str | None = Field(default=None)
    unit_price: float = Field(ge=0)
    unit_cost: float = Field(ge=0)
    items: List[SelectedOfferItem] = Field(default=[])
    additionals: List[SelectedAdditional] = Field(default=[])


PreOrderSelectedItem = Union[SelectedProduct, SelectedOffer]


class PreOrder(GenericModel):
    user_id: str = Field(example="usr_123")
    status: PreOrderStatus = Field(example=PreOrderStatus.PENDING)
    menu_id: str = Field(example="men_123")
    payment_method: PaymentMethod = Field(example=PaymentMethod.CASH)
    customer: PreOrderCustomer = Field(
        example={"name": "Ted Mosby", "ddd": "047", "phone_number": "998899889"},
    )
    delivery: Delivery = Field(
        example={
            "delivery_type": "DELIVERY",
            "address": {
                "zip_code": "89066-000",
                "city": "Blumenau",
                "neighborhood": "Bairro dos testes",
                "line_1": "Rua de teste",
                "line_2": "Casa",
                "number": "123A",
            },
        }
    )
    observation: str | None = Field(default=None, example="observation")
    items: List[PreOrderSelectedItem] = Field(default=[])
    tax: float | None = Field(default=0, example=12.2)


class UpdatePreOrder(GenericModel):
    status: PreOrderStatus = Field()


class PreOrderInDB(PreOrder, DatabaseModel):
    ...
