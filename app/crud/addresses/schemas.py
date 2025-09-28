import re
from typing import Optional

from pydantic import Field, model_validator

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel


class AddressCreate(GenericModel):
    zip_code: str = Field(example="12345-678", pattern=r"^\d{5}-?\d{3}$")
    state: str | None = Field(default=None, example="SP")
    city: str = Field(example="São Paulo")
    neighborhood: str = Field(example="Sé")
    line_1: str = Field(example="Praça da Sé")
    line_2: Optional[str] = Field(default=None, example="Complemento")
    latitude: Optional[float] = Field(default=None, example="123")
    longitude: Optional[float] = Field(default=None, example="123")

    @model_validator(mode="after")
    def validate_zip_code(self) -> "AddressCreate":
        regex = r"^\d{5}-?\d{3}$"
        if not re.match(regex, self.zip_code):
            raise ValueError("Invalid zip code value")
        self.zip_code = self.zip_code.replace("-", "")
        return self


class AddressUpdate(GenericModel):
    zip_code: Optional[str] = Field(default=None, example="12345-678", pattern=r"^\d{5}-?\d{3}$")
    state: Optional[str] = Field(default=None, example="SP")
    city: Optional[str] = Field(default=None, example="São Paulo")
    neighborhood: Optional[str] = Field(default=None, example="Sé")
    line_1: Optional[str] = Field(default=None, example="Praça da Sé")
    line_2: Optional[str] = Field(default=None, example="Complemento")
    latitude: Optional[float] = Field(default=None, example="123")
    longitude: Optional[float] = Field(default=None, example="123")


class AddressInDB(AddressCreate, DatabaseModel):
    ...
