from enum import Enum
from typing import List

from pydantic import Field, field_validator

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel


class NotificationChannel(str, Enum):
    EMAIL = "EMAIL"
    APP = "APP"


class NotificationCreate(GenericModel):
    user_id: str = Field(example="user_123")
    title: str = Field(example="Pedido atualizado")
    content: str = Field(example="Seu pedido foi enviado com sucesso!")
    channels: List[NotificationChannel] = Field(default_factory=list, min_length=1)
    notification_type: str = Field(example="SYSTEM_EVENT")

    @field_validator("channels", mode="after")
    @classmethod
    def ensure_unique_channels(cls, value: List[NotificationChannel]) -> List[NotificationChannel]:
        return list(dict.fromkeys(value))


class NotificationInDB(NotificationCreate, DatabaseModel):
    organization_id: str = Field(example="org_123")
    read: bool = Field(default=False, example=False)
