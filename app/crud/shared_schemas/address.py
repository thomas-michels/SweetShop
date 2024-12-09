from pydantic import Field
from app.core.models.base_schema import GenericModel


class Address(GenericModel):
    zip_code: str = Field(example="12345-678", pattern=r"^\d{5}-?\d{3}$")
    city: str = Field(example="Blumenau")
    neighborhood: str = Field(example="Bairro")
    line_1: str = Field(example="Rua de Testes")
    line_2: str = Field(example="Complemento")
    number: str = Field(example="123")
