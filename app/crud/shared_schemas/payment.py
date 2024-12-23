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
    method: PaymentMethod = Field(example=PaymentMethod.CASH)
    amount: float = Field(example=10, gt=0)
