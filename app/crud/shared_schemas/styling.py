from app.core.models.base_schema import GenericModel
from pydantic import Field


class Styling(GenericModel):
    primary_color: str | None = Field(default=None, example="#000000")
    secondary_color: str | None = Field(default=None, example="#111111")
