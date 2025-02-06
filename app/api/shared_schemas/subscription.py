from pydantic import Field

from app.core.models.base_schema import GenericModel


class RequestSubscription(GenericModel):
    plan_id: str = Field(example="plan_123")
    organization_id: str= Field(example="org_123")
    allow_additional: bool = Field(default=False, example=False)


class ResponseSubscription(GenericModel):
    invoice_id: str = Field(example="inv_123")
    integration_id: str = Field(example="int_123")
    init_point: str = Field(example="www.mercadopago.com.br")
