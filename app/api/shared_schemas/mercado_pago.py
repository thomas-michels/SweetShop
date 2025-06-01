from pydantic import Field
from typing import List, Optional, Union
from app.core.models.base_schema import GenericModel
from app.core.utils.utc_datetime import UTCDateTimeType


class FreeTrial(GenericModel):
    frequency: Optional[int] = Field(None, example=1)
    frequency_type: Optional[str] = Field(None, example="months")


class AutoRecurring(GenericModel):
    frequency: int = Field(..., example=12)
    frequency_type: str = Field(..., example="months")
    transaction_amount: float = Field(..., example=29.9)
    currency_id: str = Field(..., example="BRL")
    start_date: UTCDateTimeType = Field(..., example="2025-02-06T01:27:16.627-04:00")
    end_date: UTCDateTimeType = Field(..., example="2026-02-06T01:26:16.627-04:00")
    free_trial: Optional[Union[str, FreeTrial]] = Field(None, example="None")


class Summarized(GenericModel):
    quotas: int = Field(..., example=1)
    charged_quantity: Optional[Union[int, str]] = Field(None, example="None")
    pending_charge_quantity: int = Field(..., example=1)
    charged_amount: Optional[Union[float, str]] = Field(None, example="None")
    pending_charge_amount: float = Field(..., example=29.9)
    semaphore: Optional[str] = Field(None, example="None")
    last_charged_date: Optional[str] = Field(None, example="None")
    last_charged_amount: Optional[Union[float, str]] = Field(None, example="None")


class MPSubscriptionModel(GenericModel):
    id: str = Field(..., example="d0ad894de0094460a9ee3e2650031709")
    payer_id: int = Field(..., example=2026160636)
    payer_email: Optional[str] = Field(None, example="")
    back_url: str = Field(..., example="https://pedidoz.online/")
    collector_id: int = Field(..., example=131592014)
    application_id: int = Field(..., example=8659230194855501)
    status: str = Field(..., example="pending")
    reason: str = Field(..., example="pedidoZ - Básico")
    date_created: UTCDateTimeType = Field(..., example="2025-02-06T01:13:13.495-04:00")
    last_modified: UTCDateTimeType = Field(..., example="2025-02-06T01:13:13.686-04:00")
    init_point: str | None = Field(default=None, example="https://www.mercadopago.com.br/subscriptions/checkout?preapproval_id=d0ad894de0094460a9ee3e2650031709")
    auto_recurring: AutoRecurring
    summarized: Summarized
    next_payment_date: UTCDateTimeType = Field(..., example="2025-02-06T01:13:13.000-04:00")
    payment_method_id: Optional[str] = Field(None, example="None")
    payment_method_id_secondary: Optional[str] = Field(None, example="None")
    first_invoice_offset: Optional[str] = Field(None, example="None")
    subscription_id: str = Field(..., example="d0ad894de0094460a9ee3e2650031709")
    owner: Optional[str] = Field(None, example="None")


class WebhookData(GenericModel):
    id: Optional[str] = Field(None, example="123456")


class WebhookPayload(GenericModel):
    action: Optional[str] = Field(None, example="updated")
    application_id: Optional[str] = Field(None, example="8659230194855501")
    data: Optional[WebhookData] = None
    date: Optional[UTCDateTimeType] = Field(None, example="2021-11-01T02:02:02Z")
    entity: Optional[str] = Field(None, example="preapproval")
    id: Optional[str] = Field(None, example="123456")
    type: Optional[str] = Field(None, example="subscription_preapproval")
    version: Optional[int] = Field(None, example=8)


class Item(GenericModel):
    """Modelo para os itens da preferência."""
    title: str = Field(..., description="Título/descrição do item")
    quantity: int = Field(..., ge=1, description="Quantidade do item")
    unit_price: float = Field(..., ge=0, description="Preço unitário do item")
    currency_id: str = Field(default="BRL", description="ID da moeda (ex.: BRL)")


class Payer(GenericModel):
    """Modelo para informações do pagador."""
    email: str = Field(..., description="Email do pagador")
    name: Optional[str] = Field(None, description="Nome do pagador")
    surname: Optional[str] = Field(None, description="Sobrenome do pagador")


class BackUrls(GenericModel):
    """Modelo para URLs de retorno."""
    success: str = Field(..., description="URL para sucesso no pagamento")
    failure: str = Field(..., description="URL para falha no pagamento")
    pending: str = Field(..., description="URL para pagamento pendente")


class MPPreferenceModel(GenericModel):
    """Modelo para uma preferência do Mercado Pago."""
    id: str = Field(..., description="ID único da preferência")
    items: List[Item] = Field(..., description="Lista de itens da preferência")
    payer: Payer = Field(..., description="Informações do pagador")
    back_urls: BackUrls = Field(..., description="URLs de retorno após o pagamento")
    auto_return: Optional[str] = Field(None, description="Define se retorna automaticamente após aprovação")
    external_reference: Optional[str] = Field(None, description="Referência externa personalizada")
    date_created: UTCDateTimeType = Field(..., description="Data de criação da preferência")
    init_point: str = Field(..., description="URL para iniciar o fluxo de pagamento")
    sandbox_init_point: Optional[str] = Field(None, description="URL para sandbox, se aplicável")
    status: Optional[str] = Field(default="active", description="Status da preferência")

    class Config:
        # Compatibilidade com Pydantic V2
        from_attributes = True  # Permite criar instâncias a partir de atributos
        str_strip_whitespace = True  # Remove espaços em branco extras nas strings
