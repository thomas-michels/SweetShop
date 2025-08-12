from typing import List
from pydantic import Field, ConfigDict
from app.api.shared_schemas.responses import Response
from app.crud.sections.schemas import SectionInDB, CompleteSection
EXAMPLE_SECTION = {
    "id": "sec_123",
    "menu_id": "men_123",
    "name": "Doces",
    "description": "Delicious sweets",
    "is_visible": True,
    "position": 1,
    "organization_id": "org_123",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}
EXAMPLE_COMPLETE_SECTION = {
    **EXAMPLE_SECTION,
    "offers": [
        {
            "id": "off_123",
            "name": "Combo",
            "description": "Promo combo",
            "price": 10,
            "products": [{"product_id": "prod_123", "quantity": 1}],
            "file_id": "fil_123",
            "organization_id": "org_123",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "file": {
                "id": "fil_123",
                "key": "combo.png",
                "url": "http://localhost/combo.png",
                "organization_id": "org_123",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
        }
    ],
}
class GetSectionResponse(Response):
    data: CompleteSection | None = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Section found with success", "data": EXAMPLE_COMPLETE_SECTION}})
class GetSectionsResponse(Response):
    data: List[CompleteSection] = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Sections found with success", "data": [EXAMPLE_COMPLETE_SECTION]}})
class CreateSectionResponse(Response):
    data: SectionInDB | None = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Section created with success", "data": EXAMPLE_SECTION}})
class UpdateSectionResponse(Response):
    data: SectionInDB | None = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Section updated with success", "data": EXAMPLE_SECTION}})
class DeleteSectionResponse(Response):
    data: SectionInDB | None = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Section deleted with success", "data": EXAMPLE_SECTION}})
