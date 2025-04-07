from typing import List

from app.api.dependencies.get_plan_feature import get_plan_feature
from app.api.exceptions.authentication_exceptions import UnauthorizedException
from app.core.utils.features import Feature

from .repositories import TagRepository
from .schemas import Tag, TagInDB, UpdateTag


class TagServices:

    def __init__(self, tag_repository: TagRepository) -> None:
        self.__repository = tag_repository

    async def create(self, tag: Tag) -> TagInDB:
        plan_feature = await get_plan_feature(
            organization_id=self.__repository.organization_id,
            feature_name=Feature.MAX_TAGS,
        )

        quantity = await self.__repository.select_count()

        if not plan_feature or (
            plan_feature.value != "-" and (quantity + 1) >= int(plan_feature.value)
        ):
            raise UnauthorizedException(
                detail=f"Maximum number of tags reached, Max value: {plan_feature.value}"
            )

        tag_in_db = await self.__repository.create(tag=tag)
        return tag_in_db

    async def update(self, id: str, updated_tag: UpdateTag) -> TagInDB:
        tag_in_db = await self.search_by_id(id=id)

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
        tag_in_db = await self.__repository.delete_by_id(id=id)
        return tag_in_db
