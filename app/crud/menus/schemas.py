from typing import Optional

from pydantic import Field
from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel


class Menu(GenericModel):
    name: str = Field(example="Doces")
    description: str = Field(example="Bolos e tortas")
    is_visible: bool = Field(default=False, example=True)
    extra_fields: dict | None = Field(default={})

    def validate_updated_fields(self, update_menu: "UpdateMenu") -> bool:
        is_updated = False

        if update_menu.name is not None:
            self.name = update_menu.name
            is_updated = True

        if update_menu.description is not None:
            self.description = update_menu.description
            is_updated = True

        if update_menu.is_visible is not None:
            self.is_visible = update_menu.is_visible
            is_updated = True

        if update_menu.extra_fields is not None:
            self.extra_fields = update_menu.extra_fields
            is_updated = True

        return is_updated


class UpdateMenu(GenericModel):
    name: Optional[str] = Field(default=None, example="Doces")
    description: Optional[str] = Field(default=None, example="Bolos e tortas")
    is_visible: Optional[bool] = Field(default=None, example=True)
    extra_fields: Optional[dict] = Field(default=None)


class MenuInDB(Menu, DatabaseModel):
    organization_id: str = Field(example="org_123")
