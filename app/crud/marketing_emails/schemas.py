
import re
from bson import ObjectId
from enum import Enum
from pydantic import Field, field_validator, model_validator
from app.core.models.base_schema import GenericModel
from app.crud.organizations.schemas import EMAIL_REGEX


class ReasonEnum(str, Enum):
    OTHER = "OTHER"
    INSTAGRAM = "INSTAGRAM"
    FACEBOOK = "FACEBOOK"
    TIKTOK = "TIKTOK"


class MarketingEmail(GenericModel):
    name: str = Field(example="Ted Mosby")
    email: str = Field(example="ted@contact.com")
    reason: ReasonEnum = Field(example=ReasonEnum.TIKTOK.value)
    description: str | None = Field(default=None, example="pinterest")

    @model_validator(mode="after")
    def validate_model(self) -> "MarketingEmail":
        if not re.match(EMAIL_REGEX, self.email):
            raise ValueError("Invalid email")

        return self


class MarketingEmailInDB(MarketingEmail):
    id: str = Field(example="123")

    @field_validator("id", mode="before")
    def get_object_id(cls, v: str) -> str:
        if isinstance(v, ObjectId):
            return str(v)

        return v
