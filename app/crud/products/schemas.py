from enum import Enum
from typing import List, Optional
from uuid import uuid4

from pydantic import Field, model_validator

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.crud.files.schemas import FileInDB
from app.crud.tags.schemas import TagInDB


class SectionType(str, Enum):
    RADIO_GROUP = "RADIO_GROUP"
    CHECKBOX = "CHECKBOX"
    NUMBER = "NUMBER"


class Item(GenericModel):
    id: str | None = Field(default=None)
    name: str = Field(example="Bacon")
    description: str | None = Field(default=None)
    file_id: str | None = Field(default=None)
    unit_price: float = Field(ge=0)
    unit_cost: float = Field(ge=0)

    @model_validator(mode="after")
    def model_validate(self) -> "Item":
        if self.id is None:
            self.id = uuid4().hex

        return self


class CompleteItem(Item):
    file: FileInDB | None = Field(default=None)


class Section(GenericModel):
    title: str = Field(example="test")
    description: str | None = Field(default=None)
    position: int = Field(ge=1)
    type: SectionType = Field(example=SectionType.RADIO_GROUP)
    min_choices: int = Field(ge=0)
    max_choices: int = Field(ge=0)
    is_required: bool = Field(default=False)
    default_item_id: str | None = Field(default=None)
    items: List[Item] = Field(default=[])

    @model_validator(mode="after")
    def validate_section(self):
        if not self.items:
            raise ValueError("Pelo menos 1 item deve ser adicionado a seção")

        if self.type == SectionType.RADIO_GROUP:
            if self.min_choices != 1 or self.max_choices != 1:
                raise ValueError("Para o RADIO_GROUP, min_choices and max_choices precisa ser 1.")

            if not self.default_item_id:
                raise ValueError("default_item_id é necessário para o RADIO_GROUP.")

        elif self.type == SectionType.CHECKBOX or self.type == SectionType.NUMBER:
            if self.min_choices > self.max_choices:
                raise ValueError("min_choices não pode ser maior que o max_choices.")

        return self


class CompleteSection(Section):
    items: List[CompleteItem] = Field(default=[])


class Product(GenericModel):
    name: str = Field(example="Brigadeiro")
    description: str = Field(example="Brigadeiro de Leite Ninho")
    unit_price: float = Field(example=1.5)
    unit_cost: float = Field(example=0.75)
    tags: List[str] = Field(default=[])
    file_id: str | None = Field(default=None, example="fil_123")

    @model_validator(mode="after")
    def validate_price_and_cost(self) -> "Product":
        if self.unit_cost > self.unit_price:
            raise ValueError("Unit price should be greater than unit cost")

        if len(self.tags) != len(set(self.tags)):
            raise ValueError("Tags must contain unique items.")

        return self

    def validate_updated_fields(self, update_product: "UpdateProduct") -> bool:
        is_updated = False

        if update_product.name is not None:
            self.name = update_product.name
            is_updated = True

        if update_product.description is not None:
            self.description = update_product.description
            is_updated = True

        if update_product.unit_cost is not None:
            self.unit_cost = update_product.unit_cost
            is_updated = True

        if update_product.unit_price is not None:
            self.unit_price = update_product.unit_price
            is_updated = True

        if update_product.tags is not None:
            self.tags = update_product.tags
            is_updated = True

        if update_product.file_id is not None:
            self.file_id = update_product.file_id
            is_updated = True

        if update_product.sections is not None:
            self.sections = update_product.sections
            is_updated = True

        return is_updated


class UpdateProduct(GenericModel):
    name: Optional[str] = Field(default=None, example="Brigadeiro")
    description: Optional[str] = Field(default=None, example="Brigadeiro de Leite Ninho")
    unit_price: Optional[float] = Field(default=None, example=1.5)
    unit_cost: Optional[float] = Field(default=None, example=0.75)
    tags: Optional[List[str]] = Field(default=None)
    file_id: Optional[str] = Field(default=None, example="fil_123")
    sections: Optional[List[Section]] = Field(default=None)

    @model_validator(mode="after")
    def validate_price_and_cost(self) -> "Product":
        if self.unit_cost and self.unit_price:
            if self.unit_cost > self.unit_price:
                raise ValueError("Unit price should be greater than unit cost")

        if self.tags is not None:
            if len(self.tags) != len(set(self.tags)):
                raise ValueError("Tags must contain unique items.")

        return self


class ProductInDB(Product, DatabaseModel):
    organization_id: str = Field(example="org_123")


class CompleteProduct(ProductInDB):
    tags: List[str | TagInDB] = Field(default=[])
    file: str | FileInDB | None = Field(default=None)
    sections: List[CompleteSection] = Field(default=[])
