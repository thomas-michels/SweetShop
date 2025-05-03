import re
from pydantic import Field, model_validator
from app.core.models.base_schema import GenericModel


class Address(GenericModel):
    zip_code: str | None = Field(default=None, example="12345-678")
    city: str = Field(example="Blumenau")
    neighborhood: str = Field(example="Bairro")
    line_1: str = Field(example="Rua de Testes")
    line_2: str | None = Field(default=None, example="Complemento")
    number: str = Field(example="123")

    @model_validator(mode="after")
    def validate_zip_code(self):
        if self.zip_code is not None:
            regex = "^\d{5}-?\d{3}$"
            if not re.match(regex, self.zip_code):
                raise ValueError("Invalid zip code value")

        return self
