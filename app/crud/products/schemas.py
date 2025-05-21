from typing import List, Optional
from uuid import uuid4

from pydantic import Field, model_validator

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.crud.files.schemas import FileInDB
from app.crud.tags.schemas import TagInDB


class Item(GenericModel):
    id: str | None = Field(default=None)
    name: str = Field(example="Bacon")
    description: str | None = Field(default=None)
    file_id: str | None = Field(default=None)
    unit_price: float = Field(ge=0)
    unit_cost: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_item(self) -> "Item":
        if not self.id:
            self.id = uuid4().hex

        return self


class CompleteItem(Item):
    file: FileInDB | None = Field(default=None)


class ProductSection(GenericModel):
    id: str | None = Field(default=None)
    title: str = Field(example="test")
    description: str | None = Field(default=None)
    position: int | None = Field(default=1, ge=1)
    min_choices: int = Field(ge=0)
    max_choices: int = Field(ge=0)
    is_required: bool = Field(default=False)
    items: List[Item] = Field(default=[])

    def get_item_by_id(self, item_id: str) -> "Item":
        if self.items:
            for item in self.items:
                if item.id == item_id:
                    return item

    @model_validator(mode="after")
    def validate_product_section(self) -> "ProductSection":
        if not self.id:
            self.id = uuid4().hex

        if not self.items:
            raise ValueError("Pelo menos 1 item deve ser adicionado a seção")

        return self


class CompleteSection(ProductSection):
    items: List[CompleteItem] = Field(default=[])


class Product(GenericModel):
    name: str = Field(example="Brigadeiro")
    description: str = Field(example="Brigadeiro de Leite Ninho")
    unit_price: float = Field(example=1.5)
    unit_cost: float = Field(example=0.75)
    tags: List[str] = Field(default=[])
    file_id: str | None = Field(default=None, example="fil_123")
    sections: List[ProductSection] | None = Field(default=[])

    def get_section_by_id(self, section_id: str) -> "ProductSection":
        if self.sections:
            for section in self.sections:
                if section.id == section_id:
                    return section

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
    sections: Optional[List[ProductSection]] = Field(default=None)

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
