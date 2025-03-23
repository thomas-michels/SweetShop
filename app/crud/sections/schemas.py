from typing import List, Optional

from pydantic import Field
from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel


class Section(GenericModel):
    position: int = Field(example=1)
    menu_id: str = Field(example="men_123")
    name: str = Field(example="Doces")
    description: str = Field(example="Bolos e tortas")
    is_visible: bool = Field(default=False, example=True)

    def validate_updated_fields(self, update_product: "UpdateSection") -> bool:
        is_updated = False

        if update_product.name is not None:
            self.name = update_product.name
            is_updated = True

        if update_product.description is not None:
            self.description = update_product.description
            is_updated = True

        if update_product.position is not None:
            self.position = update_product.position
            is_updated = True

        if update_product.is_visible is not None:
            self.is_visible = update_product.is_visible
            is_updated = True

        return is_updated


class UpdateSection(GenericModel):
    position: Optional[int] = Field(default=None, example=1)
    menu_id: Optional[str] = Field(default=None, example="men_123")
    name: Optional[str] = Field(default=None, example="Doces")
    description: Optional[str] = Field(default=None, example="Bolos e tortas")
    is_visible: Optional[bool] = Field(default=None, example=True)


class SectionInDB(Section, DatabaseModel):
    organization_id: str = Field(example="org_123")
    offers: List[GenericModel] = Field(default=[])
