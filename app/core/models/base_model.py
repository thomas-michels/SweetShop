from pydantic import BaseModel, Field
from datetime import datetime


class DatabaseModel(BaseModel):
    id: int = Field(example=123)
    created_at: datetime = Field(example=str(datetime.now()))
    updated_at: datetime = Field(example=str(datetime.now()))
