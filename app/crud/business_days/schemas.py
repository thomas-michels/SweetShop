from pydantic import Field

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.core.utils.utc_datetime import UTCDateTime, UTCDateTimeType


class UpsertBusinessDay(GenericModel):
    menu_id: str = Field(example="men_123")
    closes_at: UTCDateTimeType = Field(example=str(UTCDateTime.now()))


class BusinessDayInDB(UpsertBusinessDay, DatabaseModel):
    organization_id: str = Field(example="org_123")
    day: str = Field(example=str(UTCDateTime.now().date()))
