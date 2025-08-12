from typing import List
from pydantic import Field, ConfigDict
from app.api.shared_schemas.responses import Response
from app.crud.invites.schemas import InviteInDB, CompleteInvite
EXAMPLE_INVITE = {
    "id": "inv_123",
    "user_email": "user@gmail.com",
    "organization_id": "org_123",
    "role": "MEMBER",
    "expires_at": "2024-01-01T00:00:00Z",
    "is_accepted": False,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}
EXAMPLE_COMPLETE_INVITE = {**EXAMPLE_INVITE, "organization": {"id": "org_123", "name": "Sweet Corp"}}
class GetInviteResponse(Response):
    data: CompleteInvite | None = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Invite found with success", "data": EXAMPLE_COMPLETE_INVITE}})
class GetInvitesByOrganizationResponse(Response):
    data: List[CompleteInvite] = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Invites found with success", "data": [EXAMPLE_COMPLETE_INVITE]}})
class GetUserInvitesResponse(Response):
    data: List[CompleteInvite] = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Invites found with success", "data": [EXAMPLE_COMPLETE_INVITE]}})
class CreateInviteResponse(Response):
    data: InviteInDB | None = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Invite created with success", "data": EXAMPLE_INVITE}})
class AcceptInviteResponse(Response):
    data: InviteInDB | None = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Invite accepted with success", "data": EXAMPLE_INVITE}})
class DeleteInviteResponse(Response):
    data: InviteInDB | None = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Invite deleted with success", "data": EXAMPLE_INVITE}})
