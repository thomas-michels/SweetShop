from pydantic import BaseModel, Field
from typing import Optional, Union
from datetime import datetime


class FreeTrial(BaseModel):
    frequency: Optional[int] = Field(None, example=1)
    frequency_type: Optional[str] = Field(None, example="months")


class AutoRecurring(BaseModel):
    frequency: int = Field(..., example=12)
    frequency_type: str = Field(..., example="months")
    transaction_amount: float = Field(..., example=29.9)
    currency_id: str = Field(..., example="BRL")
    start_date: datetime = Field(..., example="2025-02-06T01:27:16.627-04:00")
    end_date: datetime = Field(..., example="2026-02-06T01:26:16.627-04:00")
    free_trial: Optional[Union[str, FreeTrial]] = Field(None, example="None")


class Summarized(BaseModel):
    quotas: int = Field(..., example=1)
    charged_quantity: Optional[Union[int, str]] = Field(None, example="None")
    pending_charge_quantity: int = Field(..., example=1)
    charged_amount: Optional[Union[float, str]] = Field(None, example="None")
    pending_charge_amount: float = Field(..., example=29.9)
    semaphore: Optional[str] = Field(None, example="None")
    last_charged_date: Optional[str] = Field(None, example="None")
    last_charged_amount: Optional[Union[float, str]] = Field(None, example="None")


class MPSubscriptionModel(BaseModel):
    id: str = Field(..., example="d0ad894de0094460a9ee3e2650031709")
    payer_id: int = Field(..., example=2026160636)
    payer_email: Optional[str] = Field(None, example="")
    back_url: str = Field(..., example="https://pedidoz.online/")
    collector_id: int = Field(..., example=131592014)
    application_id: int = Field(..., example=8659230194855501)
    status: str = Field(..., example="pending")
    reason: str = Field(..., example="pedidoZ - Básico")
    date_created: datetime = Field(..., example="2025-02-06T01:13:13.495-04:00")
    last_modified: datetime = Field(..., example="2025-02-06T01:13:13.686-04:00")
    init_point: str = Field(..., example="https://www.mercadopago.com.br/subscriptions/checkout?preapproval_id=d0ad894de0094460a9ee3e2650031709")
    auto_recurring: AutoRecurring
    summarized: Summarized
    next_payment_date: datetime = Field(..., example="2025-02-06T01:13:13.000-04:00")
    payment_method_id: Optional[str] = Field(None, example="None")
    payment_method_id_secondary: Optional[str] = Field(None, example="None")
    first_invoice_offset: Optional[str] = Field(None, example="None")
    subscription_id: str = Field(..., example="d0ad894de0094460a9ee3e2650031709")
    owner: Optional[str] = Field(None, example="None")
