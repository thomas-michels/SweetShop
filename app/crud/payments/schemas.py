from typing import Optional

from pydantic import Field, model_validator
from app.core.models.base_model import DatabaseModel
from app.core.models.base_schema import GenericModel


from datetime import datetime
from enum import Enum
from pydantic import Field

from app.core.models.base_schema import GenericModel


class PaymentStatus(str, Enum):
    PAID = "PAID"
    PENDING = "PENDING"
    PARTIALLY_PAID = "PARTIALLY_PAID"


class PaymentMethod(str, Enum):
    PIX = "PIX"
    CASH = "CASH"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"


class Payment(GenericModel):
    order_id: str = Field(example="ord_123")
    method: PaymentMethod = Field(example=PaymentMethod.CASH)
    payment_date: datetime = Field(example=str(datetime.now()))
    amount: float = Field(example=10, gt=0)

    def validate_updated_fields(self, update_payment: "UpdatePayment") -> bool:
        is_updated = False

        if update_payment.method is not None:
            self.method = update_payment.method
            is_updated = True

        if update_payment.payment_date is not None:
            self.payment_date = update_payment.payment_date
            is_updated = True

        if update_payment.amount is not None:
            self.amount = update_payment.amount
            is_updated = True

        return is_updated


class UpdatePayment(GenericModel):
    method: Optional[PaymentMethod] = Field(default=None, example=PaymentMethod.CASH)
    payment_date: Optional[datetime] = Field(default=None, example=str(datetime.now()))
    amount: Optional[float] = Field(default=None, example=10)

    @model_validator(mode="after")
    def validate_amount(self) -> "UpdatePayment":
        if self.amount is not None:
            if self.amount < 0:
                raise ValueError("Amount should be greater than zero")

        return self


class PaymentInDB(Payment, DatabaseModel):
    ...
