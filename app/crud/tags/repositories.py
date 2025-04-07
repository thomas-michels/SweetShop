from datetime import datetime
from typing import List
from mongoengine.errors import NotUniqueError
from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository

from .models import TagModel
from .schemas import Tag, TagInDB, Styling

_logger = get_logger(__name__)


class TagRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.organization_id = organization_id

    async def create(self, tag: Tag) -> TagInDB:
        try:
            if await self.select_by_name(name=tag.name):
                raise NotUniqueError()

            tag_model = TagModel(
                organization_id=self.organization_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                **tag.model_dump()
            )
            tag_model.name = tag_model.name.strip().title()

            tag_model.save()

            return self.__build_tag(tag_model=tag_model)

        except NotUniqueError:
            _logger.warning(f"Tag with name {tag.name} is not unique")
            raise UnprocessableEntity(message="This tag is not unique")

        except Exception as error:
            _logger.error(f"Error on create_tag: {str(error)}")
            raise UnprocessableEntity(message="Error on create new Tag")

    async def update(self, tag: TagInDB) -> TagInDB:
        try:
            tag_model: TagModel = TagModel.objects(
                id=tag.id,
                is_active=True,
                organization_id=self.organization_id
            ).first()

            if tag_model:
                if tag_model.name != tag.name and await self.select_by_name(name=tag.name):
                    raise NotUniqueError()

                tag.name = tag.name.strip().title()

                tag_model.update(**tag.model_dump())

                return await self.select_by_id(id=tag_model.id)

        except NotUniqueError:
            _logger.warning(f"Tag with name {tag.name} is not unique")
            raise UnprocessableEntity(message="This tag is not unique")

        except Exception as error:
            _logger.error(f"Error on update_tag: {str(error)}")
            raise UnprocessableEntity(message="Error on update Tag")

    async def select_count(self) -> int:
        try:
            count = TagModel.objects(
                is_active=True,
                organization_id=self.organization_id,
            ).count()

            return count if count else 0

        except Exception as error:
            _logger.error(f"Error on select_count: {str(error)}")
            return 0

    async def select_by_id(self, id: str, raise_404: bool = True) -> TagInDB:
        try:
            tag_model: TagModel = TagModel.objects(
                id=id,
                is_active=True,
                organization_id=self.organization_id
            ).first()

            return self.__build_tag(tag_model=tag_model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            if raise_404:
                raise NotFoundError(message=f"Tag #{id} not found")

    async def select_by_name(self, name: str) -> TagInDB:
        try:
            name = name.strip().title()
            tag_model: TagModel = TagModel.objects(
                name=name,
                is_active=True,
                organization_id=self.organization_id
            ).first()

            if tag_model:
                return self.__build_tag(tag_model=tag_model)

        except Exception as error:
            _logger.error(f"Error on select_by_name: {str(error)}")
            raise NotFoundError(message=f"Tag with name {name} not found")

    async def select_all(self, query: str) -> List[TagInDB]:
        try:
            tags = []

            objects = TagModel.objects(
                organization_id=self.organization_id,
                is_active=True
            )

            if query:
                objects = objects.filter(name__iregex=query)

            for tag_model in objects.order_by("name"):
                tag_in_db = self.__build_tag(tag_model)

                tags.append(tag_in_db)

            return tags

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"Tags not found")

    async def delete_by_id(self, id: str) -> TagInDB:
        try:
            tag_model: TagModel = TagModel.objects(
                id=id,
                is_active=True,
                organization_id=self.organization_id
            ).first()

            if tag_model:
                tag_model.delete()

                return self.__build_tag(tag_model=tag_model)

            raise NotFoundError(message=f"Tag #{id} not found")

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Tag #{id} not found")

    def __build_tag(self, tag_model: TagModel) -> TagInDB:
        tag_in_db = TagInDB(
            id=tag_model.id,
            name=tag_model.name,
            organization_id=tag_model.organization_id,
        )

        if tag_model.styling:
            tag_in_db.styling = Styling(**dict(tag_model.styling))

        return tag_in_db
