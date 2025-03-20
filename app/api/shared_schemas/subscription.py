from pydantic import Field

from app.core.models.base_schema import GenericModel


class RequestSubscription(GenericModel):
    plan_id: str = Field(example="plan_123")
    monthly: bool = Field(default=False, example=False)
    organization_id: str= Field(example="org_123")
    allow_additional: bool = Field(default=False, example=False)
    cupoun_id: str | None = Field(default=None, example="cou_123")


class ResponseSubscription(GenericModel):
    invoice_id: str = Field(example="inv_123")
    integration_id: str = Field(example="int_123")
    init_point: str = Field(example="www.mercadopago.com.br")
    email: str = Field(example="email@gmail.com")
