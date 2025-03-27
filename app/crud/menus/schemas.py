from typing import List, Optional

from pydantic import Field
from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.crud.shared_schemas.operating_days import OperatingDay
from app.crud.shared_schemas.payment import PaymentMethod


class Menu(GenericModel):
    name: str = Field(example="Doces")
    description: str = Field(example="Bolos e tortas")
    is_visible: bool = Field(default=False, example=True)
    operating_days: List[OperatingDay] | None = Field(default=[])
    min_delivery_time: int | None = Field(default=None, example=123)
    max_delivery_time: int | None = Field(default=None, example=123)
    max_distance: int | None = Field(default=None, example=123)
    allowed_payment_methods: List[PaymentMethod] = Field(default=[], example=[PaymentMethod.CASH])
    min_order_price: float | None = Field(default=None, example=123)
    min_delivery_price: float | None = Field(default=None, example=123)
    km_tax: float | None = Field(default=None, example=123)

    def validate_updated_fields(self, update_menu: "UpdateMenu") -> bool:
        is_updated = False

        if update_menu.name is not None:
            self.name = update_menu.name
            is_updated = True

        if update_menu.description is not None:
            self.description = update_menu.description
            is_updated = True

        if update_menu.operating_days is not None:
            self.operating_days = update_menu.operating_days
            is_updated = True

        if update_menu.min_delivery_time is not None:
            self.min_delivery_time = update_menu.min_delivery_time
            is_updated = True

        if update_menu.max_delivery_time is not None:
            self.max_delivery_time = update_menu.max_delivery_time
            is_updated = True

        if update_menu.max_distance is not None:
            self.max_distance = update_menu.max_distance
            is_updated = True

        if update_menu.allowed_payment_methods is not None:
            self.allowed_payment_methods = update_menu.allowed_payment_methods
            is_updated = True

        if update_menu.min_order_price is not None:
            self.min_order_price = update_menu.min_order_price
            is_updated = True

        if update_menu.min_delivery_price is not None:
            self.min_delivery_price = update_menu.min_delivery_price
            is_updated = True

        if update_menu.km_tax is not None:
            self.km_tax = update_menu.km_tax
            is_updated = True

        return is_updated


class UpdateMenu(GenericModel):
    name: Optional[str] = Field(default=None, example="Doces")
    description: Optional[str] = Field(default=None, example="Bolos e tortas")
    is_visible: Optional[bool] = Field(default=None, example=True)
    operating_days: Optional[List[OperatingDay]] = Field(default=None)
    min_delivery_time: Optional[int] = Field(default=None, example=123)
    max_delivery_time: Optional[int] = Field(default=None, example=123)
    max_distance: Optional[int] = Field(default=None, example=123)
    allowed_payment_methods: List[PaymentMethod] = Field(default=None, example=[PaymentMethod.CASH])
    min_order_price: Optional[float] = Field(default=None, example=123)
    min_delivery_price: Optional[float] = Field(default=None, example=123)
    km_tax: Optional[float] = Field(default=None, example=123)


class MenuInDB(Menu, DatabaseModel):
    organization_id: str = Field(example="org_123")
