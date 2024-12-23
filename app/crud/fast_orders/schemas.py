from datetime import datetime
from typing import List, Optional, Type

from pydantic import Field, model_validator

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.crud.products.schemas import ProductInDB
from app.crud.shared_schemas.payment import Payment


class RequestedProduct(GenericModel):
    product_id: str = Field()
    quantity: int = Field(gt=0, example=1)


class CompleteProduct(GenericModel):
    product: ProductInDB = Field()
    quantity: int = Field(gt=0, example=1)


class FastOrder(GenericModel):
    products: List[RequestedProduct] = Field(default=[], min_length=1)
    preparation_date: datetime = Field(example=str(datetime.now()))
    description: str | None = Field(default=None, example="Description")
    payment_details: List[Payment] = Field(default=[])

    @model_validator(mode="after")
    def validate_model(self) -> "FastOrder":
        product_ids = [str(product.product_id) for product in self.products]

        if len(product_ids) != len(set(product_ids)):
            raise ValueError("Products must contain unique items.")

        return self

    def validate_updated_fields(self, update_fast_order: Type["UpdateFastOrder"]) -> bool:
        is_updated = False

        if update_fast_order.description is not None:
            self.description = update_fast_order.description
            is_updated = True

        if update_fast_order.preparation_date is not None:
            self.preparation_date = update_fast_order.preparation_date
            is_updated = True

        if update_fast_order.products is not None:
            self.products = update_fast_order.products
            is_updated = True

        if update_fast_order.payment_details is not None:
            self.payment_details = update_fast_order.payment_details
            is_updated = True

        return is_updated


class UpdateFastOrder(GenericModel):
    products: Optional[List[RequestedProduct]] = Field(default=None, min_length=1)
    preparation_date: Optional[datetime] = Field(default=None, example=str(datetime.now()))
    description: Optional[str] = Field(default=None, example="Description")
    payment_details: Optional[List[Payment]] = Field(default=None)


class FastOrderInDB(FastOrder, DatabaseModel):
    organization_id: str = Field(example="66bae5c2e59a0787e2c903e3")
    total_amount: float = Field(example=12.2)
    is_active: bool = Field(example=True, exclude=True)


class CompleteFastOrder(FastOrderInDB):
    products: List[CompleteProduct] | List[RequestedProduct] = Field(default=[], min_length=1)