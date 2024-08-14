from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime


class DatabaseModel(BaseModel):
    id: str = Field(example="123")
    created_at: datetime = Field(example=str(datetime.now()))
    updated_at: datetime = Field(example=str(datetime.now()))

    model_config = ConfigDict(extra="allow", from_attributes=True)

    @field_validator("id", mode="before")
    def get_object_id(cls, v: str) -> str:
        if isinstance(v, ObjectId):
            return str(v)

        return v
