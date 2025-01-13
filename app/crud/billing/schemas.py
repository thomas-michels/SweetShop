from pydantic import Field

from app.core.models.base_schema import GenericModel


class Billing(GenericModel):
    month: int = Field(example=1, gt=0, lt=13)
    year: int = Field(example=1)
    total_amount: float = Field(default=0, example=123)
    total_expanses: float = Field(default=0, example=123)
    payment_received: float = Field(default=0, example=123)
    cash_received: float = Field(default=0, example=123)
    pix_received: float = Field(default=0, example=123)
    credit_card_received: float = Field(default=0, example=123)
    debit_card_received: float = Field(default=0, example=123)
    pending_payments: float = Field(default=0, example=123)

    def round_numbers(self):
        self.total_amount = round(self.total_amount, 2)
        self.total_expanses = round(self.total_expanses, 2)
        self.payment_received = round(self.payment_received, 2)
        self.cash_received = round(self.cash_received, 2)
        self.pix_received = round(self.pix_received, 2)
        self.credit_card_received = round(self.credit_card_received, 2)
        self.debit_card_received = round(self.debit_card_received, 2)
        self.pending_payments = round(self.pending_payments, 2)


class ExpanseCategory(GenericModel):
    tag_id: str = Field(example="tag_123")
    tag_name: str = Field(example="Tag 123")
    total_paid: float = Field(default=0, example=123)
