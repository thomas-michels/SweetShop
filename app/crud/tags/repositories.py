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
        self.__organization_id = organization_id

    async def create(self, tag: Tag, system_tag: bool = False) -> TagInDB:
        try:
            tag_model = TagModel(
                organization_id=self.__organization_id,
                system_tag=system_tag,
                **tag.model_dump()
            )
            tag_model.name = tag_model.name.capitalize()

            tag_model.save()

            return self.__build_tag(tag_model=tag_model)

        except NotUniqueError:
            _logger.warning(f"Tag with name {tag.name} is not unique")
            return await self.select_by_name(name=tag.name)

        except Exception as error:
            _logger.error(f"Error on create_tag: {str(error)}")
            raise UnprocessableEntity(message="Error on create new Tag")

    async def update(self, tag: TagInDB) -> TagInDB:
        try:
            tag_model: TagModel = TagModel.objects(
                id=tag.id,
                system_tag=False,
                organization_id=self.__organization_id
            ).first()
            tag.name = tag.name.capitalize()

            tag_model.update(**tag.model_dump())

            return await self.select_by_id(id=tag.id)

        except Exception as error:
            _logger.error(f"Error on update_tag: {str(error)}")
            raise UnprocessableEntity(message="Error on update Tag")

    async def select_by_id(self, id: str) -> TagInDB:
        try:
            tag_model: TagModel = TagModel.objects(
                id=id,
                organization_id=self.__organization_id
            ).first()

            return self.__build_tag(tag_model=tag_model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            raise NotFoundError(message=f"Tag #{id} not found")

    async def select_by_name(self, name: str) -> TagInDB:
        try:
            name = name.capitalize()
            tag_model: TagModel = TagModel.objects(
                name=name,
                organization_id=self.__organization_id
            ).first()

            return self.__build_tag(tag_model=tag_model)

        except Exception as error:
            _logger.error(f"Error on select_by_name: {str(error)}")
            raise NotFoundError(message=f"Tag with name {name} not found")

    async def select_all(self, query: str) -> List[TagInDB]:
        try:
            tags = []

            if query:
                objects = TagModel.objects(
                    name__iregex=query,
                    organization_id=self.__organization_id
                )

            else:
                objects = TagModel.objects(organization_id=self.__organization_id).order_by("name")

            for tag_model in objects:
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
                system_tag=False,
                organization_id=self.__organization_id
            ).first()
            tag_model.delete()

            return self.__build_tag(tag_model=tag_model)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Tag #{id} not found")

    def __build_tag(self, tag_model: TagModel) -> TagInDB:
        tag_in_db = TagInDB(
            id=tag_model.id,
            name=tag_model.name,
            organization_id=tag_model.organization_id,
            system_tag=tag_model.system_tag
        )

        if tag_model.styling:
            tag_in_db.styling = Styling(**dict(tag_model.styling))

        return tag_in_db
