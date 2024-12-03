from pydantic import Field, BaseModel
from app.crud.organizations.schemas import RoleEnum


class RequestRole(BaseModel):
    role: RoleEnum = Field(example=RoleEnum.MEMBER)
