from pydantic import ConfigDict, Field

from app.api.shared_schemas.responses import Response
from app.crud.business_days.schemas import BusinessDayInDB

EXAMPLE_BUSINESS_DAY = {
    "id": "bsd_123",
    "menuId": "men_123",
    "organizationId": "org_123",
    "day": "2025-09-23",
    "closesAt": "2025-09-23T14:30:00Z",
    "createdAt": "2025-09-23T04:17:34.339000+00:00",
    "updatedAt": "2025-09-23T04:17:34.339000+00:00",
}


class UpsertBusinessDayResponse(Response):
    data: BusinessDayInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Business day saved with success",
                "data": EXAMPLE_BUSINESS_DAY,
            }
        }
    )


class GetBusinessDayResponse(Response):
    data: BusinessDayInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Business day found with success",
                "data": EXAMPLE_BUSINESS_DAY,
            }
        }
    )
