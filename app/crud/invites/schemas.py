from pydantic import Field

from app.core.models.base_model import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.core.utils.utc_datetime import UTCDateTime, UTCDateTimeType
from app.crud.organizations.schemas import OrganizationInDB
from app.crud.shared_schemas.roles import RoleEnum


class Invite(GenericModel):
    user_email: str = Field(example="user@gmail.com")
    organization_id: str = Field(example="org_123")
    role: RoleEnum = Field(example=RoleEnum.MEMBER.value)
    expires_at: UTCDateTimeType | None = Field(default=None, example=str(UTCDateTime.now()))


class InviteInDB(Invite, DatabaseModel):
    is_accepted: bool = Field(default=False, example=False)


class CompleteInvite(InviteInDB):
    organization_id: str = Field(example="org_123", exclude=True)
    organization: OrganizationInDB | None = Field(default=None)
