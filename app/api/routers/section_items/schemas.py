from typing import List

from pydantic import Field, ConfigDict

from app.api.shared_schemas.responses import Response
from app.crud.section_items import SectionItemInDB

EXAMPLE_SECTION_ITEM = {
    "id": "sci_123",
    "section_id": "sec_123",
    "item_id": "item_123",
    "item_type": "PRODUCT",
    "position": 1,
    "is_visible": True,
    "organization_id": "org_123",
}


class GetSectionItemsResponse(Response):
    data: List[SectionItemInDB] = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Section items found with success",
                "data": [
                    EXAMPLE_SECTION_ITEM,
                    {**EXAMPLE_SECTION_ITEM, "id": "sci_456", "position": 2},
                ],
            }
        }
    )


class CreateSectionItemResponse(Response):
    data: SectionItemInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"message": "Section item created with success", "data": EXAMPLE_SECTION_ITEM}
        }
    )


class UpdateSectionItemResponse(Response):
    data: SectionItemInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"message": "Section item updated with success", "data": EXAMPLE_SECTION_ITEM}
        }
    )


class DeleteSectionItemResponse(Response):
    data: SectionItemInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"message": "Section item deleted with success", "data": EXAMPLE_SECTION_ITEM}
        }
    )
