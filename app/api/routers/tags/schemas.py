from typing import List

from pydantic import Field, ConfigDict

from app.api.shared_schemas.responses import Response, ListResponseSchema
from app.crud.tags import TagInDB

EXAMPLE_TAG = {
    "id": "tag_123",
    "name": "Street Mode",
    "styling": {
        "font_color": "#000000",
        "primary_color": "#000000",
        "secondary_color": "#111111",
    },
}


class GetTagResponse(Response):
    data: TagInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"message": "Tag found with success", "data": EXAMPLE_TAG}
        }
    )


class GetTagsResponse(ListResponseSchema):
    data: List[TagInDB] = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Tags found with success",
                "pagination": {"page": 1, "page_size": 2, "total": 2},
                "data": [
                    EXAMPLE_TAG,
                    {**EXAMPLE_TAG, "id": "tag_456", "name": "VIP"},
                ],
            }
        }
    )


class CreateTagResponse(Response):
    data: TagInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"message": "Tag created with success", "data": EXAMPLE_TAG}
        }
    )


class UpdateTagResponse(Response):
    data: TagInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"message": "Tag updated with success", "data": EXAMPLE_TAG}
        }
    )


class DeleteTagResponse(Response):
    data: TagInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"message": "Tag deleted with success", "data": EXAMPLE_TAG}
        }
    )
