from typing import List

from app.api.exceptions.authentication_exceptions import BadRequestException
from .schemas import Tag, TagInDB, UpdateTag
from .repositories import TagRepository


class TagServices:

    def __init__(self, tag_repository: TagRepository) -> None:
        self.__repository = tag_repository

    async def create(self, tag: Tag, system_tag: bool = False) -> TagInDB:
        tag_in_db = await self.__repository.create(tag=tag, system_tag=system_tag)
        return tag_in_db

    async def update(self, id: str, updated_tag: UpdateTag) -> TagInDB:
        tag_in_db = await self.search_by_id(id=id)

        if tag_in_db.system_tag:
            raise BadRequestException(detail="You cannot update this tag!")

        is_updated = tag_in_db.validate_updated_fields(update_tag=updated_tag)

        if is_updated:
            tag_in_db = await self.__repository.update(tag=tag_in_db)

        return tag_in_db

    async def search_by_id(self, id: str) -> TagInDB:
        tag_in_db = await self.__repository.select_by_id(id=id)
        return tag_in_db

    async def search_all(self, query: str) -> List[TagInDB]:
        tags = await self.__repository.select_all(query=query)
        return tags

    async def delete_by_id(self, id: str) -> TagInDB:
        tag_in_db = await self.search_by_id(id=id)

        if tag_in_db.system_tag:
            raise BadRequestException(detail="You cannot delete this tag!")

        tag_in_db = await self.__repository.delete_by_id(id=id)
        return tag_in_db