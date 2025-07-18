from typing import List

from app.api.dependencies.email_sender import send_email
from app.api.exceptions.authentication_exceptions import BadRequestException, UnauthorizedException, UnprocessableEntityException
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.organizations.repositories import OrganizationRepository
from app.crud.shared_schemas.roles import RoleEnum
from app.crud.users.repositories import UserRepository

from .schemas import CompleteInvite, Invite, InviteInDB
from .repositories import InviteRepository


class InviteServices:

    def __init__(
            self,
            invite_repository: InviteRepository,
            user_repository: UserRepository,
            organization_repository: OrganizationRepository,
        ) -> None:
        self.__invite_repository = invite_repository
        self.__user_repository = user_repository
        self.__organization_repository = organization_repository

    async def create(self, invite: Invite, user_making_request: str) -> InviteInDB:
        user_making_request_in_db = await self.__user_repository.select_by_id(id=user_making_request)

        if invite.user_email == user_making_request_in_db.email:
            raise UnprocessableEntityException(detail="You cannot create an invite for you!")

        if invite.role == RoleEnum.OWNER:
            raise UnauthorizedException(detail="You cannot invite a new owner of an organization!")

        if invite.expires_at and invite.expires_at <= UTCDateTime.now():
            raise UnprocessableEntityException(detail="Expires at should be grater than now!")

        user_in_db = await self.__user_repository.select_by_email(email=invite.user_email, raise_404=False)

        organization_in_db = await self.__organization_repository.select_by_id(id=invite.organization_id)

        user_organization = organization_in_db.get_user_in_organization(user_id=user_making_request)

        if not user_organization or user_organization.role not in [RoleEnum.OWNER, RoleEnum.ADMIN, RoleEnum.MANAGER]:
            raise UnauthorizedException(detail="You cannot create invites for this organization!")

        current_role = user_organization.role

        if current_role == RoleEnum.ADMIN and invite.role == RoleEnum.ADMIN:
            raise UnauthorizedException(detail="You cannot invite someone with this role!")

        if current_role == RoleEnum.MANAGER and invite.role in [RoleEnum.ADMIN, RoleEnum.MANAGER]:
            raise UnauthorizedException(detail="You cannot invite someone with this role!")

        if user_in_db:
            if organization_in_db.get_user_in_organization(user_id=user_in_db.user_id):
                raise BadRequestException(detail="User is already a participant of the organization")

        invite_in_db = await self.__invite_repository.create(invite=invite)

        with open("./templates/email.html", mode="r", encoding="UTF-8") as file:
            message = file.read()
            message = message.replace("$ORGANIZATION_NAME$", organization_in_db.name)
            message = message.replace("$USER_NAME$", user_making_request_in_db.name)
            message = message.replace("$EXPIRES_DATE$", invite_in_db.expires_at.strftime("%d/%m/%Y") if invite_in_db.expires_at else "INDEFINIDO")

        send_email(
            email_to=[invite.user_email],
            title=f"pedidoZ - Você recebeu um convite de {organization_in_db.name}",
            message=message
        )

        return invite_in_db

    async def accept(self, id: str, user_making_request: str) -> InviteInDB:
        invite_in_db = await self.search_by_id(id=id)

        user_in_db = await self.__user_repository.select_by_id(id=user_making_request)

        if invite_in_db.user_email != user_in_db.email:
            raise BadRequestException(detail="You cannot accept this invite!")

        invite_in_db.is_accepted = True
        invite_in_db = await self.__invite_repository.update(invite=invite_in_db)

        return invite_in_db

    async def search_by_id(self, id: str) -> InviteInDB:
        invite_in_db = await self.__invite_repository.select_by_id(id=id)
        return invite_in_db

    async def search_by_user_id(self, user_id: str, accepted: bool = None, expand: List[str] = []) -> List[InviteInDB]:
        user_in_db = await self.__user_repository.select_by_id(id=user_id)

        invites = await self.__invite_repository.select_by_email(
            user_email=user_in_db.email,
            accepted=accepted
        )

        if not expand:
            return invites

        complete_invites = []

        for invite in invites:
            complete_invite = await self.__build_complete_invite(invite=invite, expand=expand)
            complete_invites.append(complete_invite)

        return complete_invites

    async def search_all(self, organization_id: str, accepted: bool = None, expand: List[str] = []) -> List[InviteInDB]:
        invites = await self.__invite_repository.select_all(
            organization_id=organization_id,
            accepted=accepted
        )

        if not expand:
            return invites

        complete_invites = []

        for invite in invites:
            complete_invite = await self.__build_complete_invite(invite=invite, expand=expand)
            complete_invites.append(complete_invite)

        return complete_invites

    async def delete_by_id(self, id: str, user_making_request: str) -> InviteInDB:
        user_in_db = await self.__user_repository.select_by_id(id=user_making_request)

        invite_in_db = await self.__invite_repository.select_by_id(id=id)

        organization_in_db = await self.__organization_repository.select_by_id(
            id=invite_in_db.organization_id
        )

        user_role = organization_in_db.get_user_in_organization(user_id=user_making_request)

        if invite_in_db.user_email == user_in_db.email or (user_role and user_role.role != RoleEnum.MEMBER):
            invite_in_db = await self.__invite_repository.delete_by_id(id=id)
            return invite_in_db

    async def __build_complete_invite(self, invite: InviteInDB, expand: List[str]) -> CompleteInvite:
        complete_invite = CompleteInvite(**invite.model_dump())

        if "organizations" in expand:
            organization_in_db = await self.__organization_repository.select_by_id(invite.organization_id)
            complete_invite.organization = organization_in_db

        return complete_invite
