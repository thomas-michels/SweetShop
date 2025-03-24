from typing import Optional

from pydantic import Field
from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel


class Section(GenericModel):
    position: int = Field(example=1)
    menu_id: str = Field(example="men_123")
    name: str = Field(example="Doces")
    description: str = Field(example="Bolos e tortas")
    is_visible: bool = Field(default=False, example=True)

    def validate_updated_fields(self, update_section: "UpdateSection") -> bool:
        is_updated = False

        if update_section.name is not None:
            self.name = update_section.name
            is_updated = True

        if update_section.description is not None:
            self.description = update_section.description
            is_updated = True

        if update_section.position is not None:
            self.position = update_section.position
            is_updated = True

        if update_section.is_visible is not None:
            self.is_visible = update_section.is_visible
            is_updated = True

        return is_updated


class UpdateSection(GenericModel):
    position: Optional[int] = Field(default=None, example=1)
    name: Optional[str] = Field(default=None, example="Doces")
    description: Optional[str] = Field(default=None, example="Bolos e tortas")
    is_visible: Optional[bool] = Field(default=None, example=True)


class SectionInDB(Section, DatabaseModel):
    organization_id: str = Field(example="org_123")
