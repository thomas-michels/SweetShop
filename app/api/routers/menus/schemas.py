from typing import List

from pydantic import Field, ConfigDict

from app.api.shared_schemas.responses import Response, ListResponseSchema
from app.crud.menus.schemas import MenuInDB

EXAMPLE_MENU = {
    "id": "menu_123",
    "name": "Doces",
    "description": "Bolos e tortas",
    "is_visible": True,
    "slug": "doces",
    "organization_id": "org_123",
    "accepts_outside_business_hours": False,
}


class GetMenuResponse(Response):
    data: MenuInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"message": "Menu found with success", "data": EXAMPLE_MENU}
        }
    )


class GetMenusResponse(ListResponseSchema):
    data: List[MenuInDB] = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Menus found with success",
                "pagination": {"page": 1, "page_size": 2, "total": 2},
                "data": [
                    EXAMPLE_MENU,
                    {**EXAMPLE_MENU, "id": "menu_456", "name": "Salgados"},
                ],
            }
        }
    )


class CreateMenuResponse(Response):
    data: MenuInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"message": "Menu created with success", "data": EXAMPLE_MENU}
        }
    )


class UpdateMenuResponse(Response):
    data: MenuInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"message": "Menu updated with success", "data": EXAMPLE_MENU}
        }
    )


class DeleteMenuResponse(Response):
    data: MenuInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"message": "Menu deleted with success", "data": EXAMPLE_MENU}
        }
    )
