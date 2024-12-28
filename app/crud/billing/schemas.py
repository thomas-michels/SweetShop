from pydantic import Field

from app.core.models.base_schema import GenericModel


class Billing(GenericModel):
    month: int = Field(example=1, gt=0, lt=13)
    total_amount: float = Field(default=0, example=123, max_digits=2)
    total_amount_last_month: float = Field(default=0, example=123, max_digits=2)
    total_expanses: float = Field(default=0, example=123, max_digits=2)
    total_expanses_last_month: float = Field(default=0, example=123, max_digits=2)
    payment_received: float = Field(default=0, example=123, max_digits=2)
    cash_received: float = Field(default=0, example=123, max_digits=2)
    pix_received: float = Field(default=0, example=123, max_digits=2)
    credit_card_received: float = Field(default=0, example=123, max_digits=2)
    debit_card_received: float = Field(default=0, example=123, max_digits=2)
    payment_received_last_month: float = Field(default=0, example=123, max_digits=2)
    pending_payments: float = Field(default=0, example=123, max_digits=2)
