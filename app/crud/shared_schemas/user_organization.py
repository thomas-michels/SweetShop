from pydantic import Field
from app.core.models.base_schema import GenericModel
from app.crud.shared_schemas.roles import RoleEnum


class UserOrganization(GenericModel):
    user_id: str = Field(example="user_123")
    role: RoleEnum = Field(example=RoleEnum.ADMIN.value)
