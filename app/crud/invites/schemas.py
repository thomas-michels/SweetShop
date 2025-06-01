from pydantic import Field, model_validator

from app.core.models.base_model import DatabaseModel
from app.core.models.base_schema import GenericModel, convert_datetime_to_realworld
from app.core.utils.utc_datetime import UTCDateTime, UTCDateTimeType
from app.crud.organizations.schemas import OrganizationInDB
from app.crud.shared_schemas.roles import RoleEnum


class Invite(GenericModel):
    user_email: str = Field(example="user@gmail.com")
    organization_id: str = Field(example="org_123")
    role: RoleEnum = Field(example=RoleEnum.MEMBER.value)
    expires_at: UTCDateTimeType | None = Field(default=None, example=str(UTCDateTime.now()))

    @model_validator(mode="after")
    def validate_expires_at(self):
        if self.expires_at:
            self.expires_at = convert_datetime_to_realworld(dt=self.expires_at)

        return self


class InviteInDB(Invite, DatabaseModel):
    is_accepted: bool = Field(default=False, example=False)


class CompleteInvite(InviteInDB):
    organization_id: str = Field(example="org_123", exclude=True)
    organization: OrganizationInDB | None = Field(default=None)
