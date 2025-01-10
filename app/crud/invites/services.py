from typing import List

from .schemas import Invite, InviteInDB
from .repositories import InviteRepository


class InviteServices:

    def __init__(self, invite_repository: InviteRepository) -> None:
        self.__repository = invite_repository

    async def create(self, invite: Invite) -> InviteInDB:
        # TODO 
        invite_in_db = await self.__repository.create(invite=invite)

        # TODO add send email here

        return invite_in_db

    async def accept(self, id: str, user_making_request: str) -> InviteInDB:
        invite_in_db = await self.search_by_id(id=id)

        # Add logic to check if the user accepting the invite is the same of the invite
        # if invite_in_db.user_email

        # TODO add logic to accept an invite

        # if is_updated:
        #     invite_in_db = await self.__repository.update(invite=invite_in_db)

        # return invite_in_db

    async def search_by_id(self, id: str) -> InviteInDB:
        invite_in_db = await self.__repository.select_by_id(id=id)
        return invite_in_db

    async def search_by_user_id(self, user_id: str) -> List[InviteInDB]:
        ...
        # invite_in_db = await self.__repository.select_by_id(id=id)
        # return invite_in_db

    async def search_all(self) -> List[InviteInDB]:
        invites = await self.__repository.select_all()
        return invites

    async def delete_by_id(self, id: str) -> InviteInDB:
        invite_in_db = await self.__repository.delete_by_id(id=id)
        return invite_in_db
