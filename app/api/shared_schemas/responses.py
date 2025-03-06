from typing import List
from pydantic import BaseModel, Field, SerializeAsAny


class MessageResponse(BaseModel):
    message: str = Field(example="Success")


class Response(MessageResponse):
    data: SerializeAsAny[BaseModel] | SerializeAsAny[List[BaseModel]] | None = Field()
