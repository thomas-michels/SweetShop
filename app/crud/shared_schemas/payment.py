from enum import Enum
from pydantic import Field
from app.core.models.base_schema import GenericModel
from app.core.utils.utc_datetime import UTCDateTime, UTCDateTimeType


class PaymentStatus(str, Enum):
    PAID = "PAID"
    PENDING = "PENDING"
    PARTIALLY_PAID = "PARTIALLY_PAID"


class PaymentMethod(str, Enum):
    PIX = "PIX"
    CASH = "CASH"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    ZELLE = "ZELLE"


class Payment(GenericModel):
    method: PaymentMethod = Field(example=PaymentMethod.CASH)
    payment_date: UTCDateTimeType = Field(example=str(UTCDateTime.now()))
    amount: float = Field(example=10, gt=0)
