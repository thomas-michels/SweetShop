from pydantic import Field, model_validator
from enum import Enum
from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel


class MessageType(str, Enum):
    INFORMATION = "INFORMATION"
    ALERT = "ALERT"


class Origin(str, Enum):
    ORDERS = "ORDERS"
    PLANS = "PLANS"


class Message(GenericModel):
    international_code: str = Field(default=None, example="55")
    ddd: str = Field(default=None, example="047", max_length=3)
    phone_number: str = Field(default=None, max_length=9)
    origin: Origin = Field(example=Origin.ORDERS)
    message: str = Field(example="Raw message")
    message_type: MessageType = Field(example=MessageType.INFORMATION)
    integration_id: str | None = Field(default=None)

    @model_validator(mode="after")
    def validate_model(self) -> "Message":
        if self.international_code == "55":
            if self.ddd.startswith("0"):
                self.ddd = self.ddd[1:]

        return self


class MessageInDB(Message, DatabaseModel):
    organization_id: str = Field(example="org_123")
