from typing import List
from pydantic import Field, ConfigDict
from app.api.shared_schemas.responses import Response
from app.crud.organizations.schemas import OrganizationInDB, CompleteOrganization
EXAMPLE_ORGANIZATION = {
    "id": "org_123",
    "name": "Sweet Corp",
    "ddd": "047",
    "phone_number": "999888777",
    "address": {
        "zip_code": "89000-000",
        "city": "Blumenau",
        "neighborhood": "Centro",
        "line_1": "Rua das Flores",
        "number": "100",
    },
    "email": "contact@sweetcorp.com",
    "document": "11155521999",
    "currency": "BRL",
    "language": "PORTUGUESE",
    "file_id": "fil_123",
    "unit_distance": "KM",
    "tax": 10,
    "website": "https://sweetcorp.com",
    "social_links": {
        "tiktok": "https://tiktok.com/@sweetcorp",
        "instagram": "https://instagram.com/sweetcorp",
        "x": "https://x.com/sweetcorp",
        "facebook": "https://facebook.com/sweetcorp",
        "google_profile": "https://g.page/sweetcorp",
    },
    "styling": {
        "primary_color": "#111111",
        "secondary_color": "#222222",
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}
EXAMPLE_COMPLETE_ORGANIZATION = {
    **EXAMPLE_ORGANIZATION,
    "users": [
        {
            "role": "ADMIN",
            "user": {
                "user_id": "usr_123",
                "email": "owner@sweetcorp.com",
                "name": "Owner",
                "nickname": "owner",
                "picture": None,
                "user_metadata": {},
                "app_metadata": {},
                "last_login": "2024-01-01T00:00:00Z",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
        }
    ],
    "plan": {"id": "plan_123", "name": "Free", "price": 0, "currency": "BRL"},
    "file": {
        "id": "fil_123",
        "key": "logo.png",
        "url": "http://localhost/logo.png",
        "organization_id": "org_123",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    },
}
class GetUsersOrganizationsResponse(Response):
    data: List[CompleteOrganization] = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Organization found with success", "data": [EXAMPLE_COMPLETE_ORGANIZATION]}})
class GetOrganizationResponse(Response):
    data: CompleteOrganization | None = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Organization found with success", "data": EXAMPLE_COMPLETE_ORGANIZATION}})
class GetOrganizationsResponse(Response):
    data: List[CompleteOrganization] = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Organizations found with success", "data": [EXAMPLE_COMPLETE_ORGANIZATION]}})
class CreateOrganizationResponse(Response):
    data: OrganizationInDB | None = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Organization created with success", "data": EXAMPLE_ORGANIZATION}})
class UpdateOrganizationResponse(Response):
    data: OrganizationInDB | None = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Organization updated with success", "data": EXAMPLE_ORGANIZATION}})
class DeleteOrganizationResponse(Response):
    data: OrganizationInDB | None = Field()
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Organization deleted with success", "data": EXAMPLE_ORGANIZATION}})
class UpdateUserRoleResponse(Response):
    data: None = Field(default=None)
    model_config = ConfigDict(json_schema_extra={"example": {"message": "User's role updated with success", "data": None}})
class RemoveUserFromOrganizationResponse(Response):
    data: None = Field(default=None)
    model_config = ConfigDict(json_schema_extra={"example": {"message": "User removed from Organization with success", "data": None}})
class TransferOrganizationOwnershipResponse(Response):
    data: None = Field(default=None)
    model_config = ConfigDict(json_schema_extra={"example": {"message": "New organization owner set with success", "data": None}})
class LeaveOrganizationResponse(Response):
    data: None = Field(default=None)
    model_config = ConfigDict(json_schema_extra={"example": {"message": "You left the organization", "data": None}})
class GetOrganizationFeatureResponse(Response):
    data: None = Field(default=None)
    model_config = ConfigDict(json_schema_extra={"example": {"message": "This organization have this feature", "data": None}})
