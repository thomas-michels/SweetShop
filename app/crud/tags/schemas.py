from typing import Optional

from bson import ObjectId
from pydantic import ConfigDict, Field, field_validator
from app.core.models.base_schema import GenericModel


class Styling(GenericModel):
    font_color: str = Field(example="#000000")
    primary_color: str = Field(example="#000000")
    secondary_color: str = Field(example="#111111")


class Tag(GenericModel):
    name: str = Field(example="Street Mode")
    styling: Styling | None = Field(default=None)

    def validate_updated_fields(self, update_tag: "UpdateTag") -> bool:
        is_updated = False

        if update_tag.name is not None:
            self.name = update_tag.name
            is_updated = True

        if update_tag.styling is not None:
            self.styling = update_tag.styling
            is_updated = True

        return is_updated


class UpdateTag(GenericModel):
    name: Optional[str] = Field(default=None, example="Ted Mosby")
    styling: Optional[Styling] = Field(default=None)


class TagInDB(Tag):
    id: str = Field(example="123")
    organization_id: str = Field(example="org_123", exclude=True)
    system_tag: bool = Field(default=False, example=False, exclude=True)

    model_config = ConfigDict(extra="allow", from_attributes=True)

    @field_validator("id", mode="before")
    def get_object_id(cls, v: str) -> str:
        if isinstance(v, ObjectId):
            return str(v)

        return v

    @field_validator("styling", mode="before")
    def get_styling(cls, v: str) -> dict | None:
        if isinstance(v, dict):
            return None

        return v
