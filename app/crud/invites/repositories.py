from typing import List
from mongoengine import Q
from mongoengine.errors import NotUniqueError
from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository
from app.core.utils.utc_datetime import UTCDateTime

from .models import InviteModel
from .schemas import Invite, InviteInDB

_logger = get_logger(__name__)


class InviteRepository(Repository):
    def __init__(self) -> None:
        super().__init__()

    async def create(self, invite: Invite) -> InviteInDB:
        try:
            await self.validate_if_is_not_duplicated(invite_in_db=invite)

            invite_model = InviteModel(
                is_accepted=False,
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
                **invite.model_dump(),
            )
            invite_model.user_email = invite_model.user_email.lower()

            invite_model.save()

            return InviteInDB.model_validate(invite_model)

        except NotUniqueError:
            _logger.warning(
                f"Duplicated invite for email {invite.user_email} and organization {invite.organization_id}!"
            )
            raise UnprocessableEntity(
                message="This user already has an active invitation for this organization!"
            )

        except Exception as error:
            _logger.error(f"Error on create_invite: {str(error)}")
            raise UnprocessableEntity(message="Error on create new Invite")

    async def update(self, invite: InviteInDB) -> InviteInDB:
        try:
            invite_model: InviteModel = InviteModel.objects(
                id=invite.id,
            ).first()

            invite.user_email = invite.user_email.lower()
            invite_model.update(**invite.model_dump())

            return await self.select_by_id(id=invite.id)

        except Exception as error:
            _logger.error(f"Error on update_invite: {str(error)}")
            raise UnprocessableEntity(message="Error on update Invite")

    async def select_by_id(self, id: str, raise_404: bool = True) -> InviteInDB:
        try:
            invite_model: InviteModel = InviteModel.objects(
                id=id,
            ).first()

            return InviteInDB.model_validate(invite_model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            if raise_404:
                raise NotFoundError(message=f"Invite #{id} not found")

    async def select_by_email(
        self, user_email: str, accepted: bool = None
    ) -> List[InviteInDB]:
        try:
            user_email = user_email.lower()

            objects: InviteModel = InviteModel.objects(
                user_email=user_email,
            )

            if accepted is not None:
                objects = objects.filter(is_accepted=accepted)

            now = UTCDateTime.now()

            objects = objects.filter(
                (Q(expires_at__exists=False) | Q(expires_at__gt=now))
            )

            invites = []

            for invite_model in objects.order_by("user_email"):
                invites.append(InviteInDB.model_validate(invite_model))

            return invites

        except Exception as error:
            _logger.error(f"Error on select_by_email: {str(error)}")
            raise NotFoundError(message=f"Invite with email {user_email} not found")

    async def select_all(
        self, organization_id: str, accepted: bool = None
    ) -> List[InviteInDB]:
        try:
            invites = []

            objects = InviteModel.objects(organization_id=organization_id)

            if accepted is not None:
                objects = objects.filter(is_accepted=accepted)

            now = UTCDateTime.now()

            objects = objects.filter(
                (Q(expires_at__exists=False) | Q(expires_at__gt=now))
            )

            for invite_model in objects.order_by("user_email"):
                invites.append(InviteInDB.model_validate(invite_model))

            return invites

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message="Invites not found")

    async def delete_by_id(self, id: str) -> InviteInDB:
        try:
            invite_model: InviteModel = InviteModel.objects(
                id=id,
            ).first()
            invite_model.delete()

            return InviteInDB.model_validate(invite_model)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Invite #{id} not found")

    async def validate_if_is_not_duplicated(self, invite_in_db: Invite) -> None:
        invites = await self.select_by_email(
            user_email=invite_in_db.user_email, accepted=False
        )

        for invite in invites:
            if invite.organization_id == invite_in_db.organization_id:
                raise NotUniqueError()
