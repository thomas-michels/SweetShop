
from datetime import datetime
from pydantic import Field

from app.core.models.base_model import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.crud.organizations.schemas import RoleEnum


class Invite(GenericModel):
    user_email: str = Field(example="user@gmail.com")
    role: RoleEnum = Field(example=RoleEnum.MEMBER.value)
    expires_at: datetime | None = Field(default=None, example=str(datetime.now()))


class InviteInDB(Invite, DatabaseModel):
    organization_id: str = Field(example="org_123", exclude=True)
    is_accepted: bool = Field(default=False, example=False)
