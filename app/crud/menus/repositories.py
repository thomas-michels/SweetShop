from typing import List, Optional
from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository
from app.core.utils import slugify
from app.core.utils.utc_datetime import UTCDateTime

from .models import MenuModel
from .schemas import Menu, MenuInDB

_logger = get_logger(__name__)


class MenuRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.organization_id = organization_id

    async def create(self, menu: Menu) -> MenuInDB:
        if await self.select_by_name(name=menu.name, raise_404=False):
            raise UnprocessableEntity("Um catálogo com esse nome já existe")

        try:
            menu_data = menu.model_dump()
            formatted_name = menu_data.get("name", "")
            formatted_name = formatted_name.title()
            menu_data["name"] = formatted_name
            menu_data["slug"] = slugify(formatted_name)

            if not menu_data["slug"]:
                raise UnprocessableEntity("Nome de catálogo inválido")

            menu_model = MenuModel(
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
                organization_id=self.organization_id,
                **menu_data,
            )

            menu_model.save()
            _logger.info(
                f"Menu {formatted_name} saved for organization {self.organization_id}"
            )

            return MenuInDB.model_validate(menu_model)

        except Exception as error:
            _logger.error(f"Error on create_menu: {str(error)}")
            raise UnprocessableEntity(message="Error on create new menu")

    async def update(self, menu: MenuInDB) -> MenuInDB:
        menu_with_same_name = await self.select_by_name(name=menu.name, raise_404=False)
        if menu_with_same_name and menu_with_same_name.id != menu.id:
            raise UnprocessableEntity("Um catálogo com esse nome já existe")

        try:
            menu_model: MenuModel = MenuModel.objects(
                id=menu.id, is_active=True, organization_id=self.organization_id
            ).first()
            menu.name = menu.name.title()
            menu.slug = slugify(menu.name)

            if not menu.slug:
                raise UnprocessableEntity("Nome de catálogo inválido")

            menu_model.update(**menu.model_dump())

            return await self.select_by_id(id=menu.id)

        except Exception as error:
            _logger.error(f"Error on update_menu: {str(error)}")
            raise UnprocessableEntity(message="Error on update menu")

    async def select_count(self, query: str, is_visible: bool = None) -> int:
        try:
            objects = MenuModel.objects(
                is_active=True,
                organization_id=self.organization_id,
            )

            if query:
                slug_query = slugify(query)

                if slug_query:
                    objects = objects.filter(slug__icontains=slug_query)

            if is_visible is not None:
                objects = objects.filter(is_visible=is_visible)

            return max(objects.count(), 0)

        except Exception as error:
            _logger.error(f"Error on select_count: {str(error)}")
            return 0

    async def select_by_id(self, id: str, raise_404: bool = True) -> MenuInDB:
        try:
            menu_model: MenuModel = MenuModel.objects(
                id=id, is_active=True, organization_id=self.organization_id
            ).first()

            return MenuInDB.model_validate(menu_model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            if raise_404:
                raise NotFoundError(message=f"Menu #{id} not found")

    async def select_by_name(self, name: str, raise_404: bool = True) -> MenuInDB:
        try:
            slug = slugify(name)
            menu_model: Optional[MenuModel] = None

            if slug:
                menu_model = MenuModel.objects(
                    slug=slug, is_active=True, organization_id=self.organization_id
                ).first()

            if not menu_model:
                menu_model = MenuModel.objects(
                    name__iexact=name,
                    is_active=True,
                    organization_id=self.organization_id,
                ).first()

            if menu_model:
                return MenuInDB.model_validate(menu_model)

            if raise_404:
                raise NotFoundError(message=f"Menu with name {name} not found")

        except Exception as error:
            _logger.error(f"Error on select_by_name: {str(error)}")
            if raise_404:
                raise NotFoundError(message=f"Menu with name {name} not found")

    async def select_all(
        self,
        query: str,
        is_visible: bool = None,
        page: int = None,
        page_size: int = None,
    ) -> List[MenuInDB]:
        try:
            menus = []

            objects = MenuModel.objects(
                is_active=True, organization_id=self.organization_id
            )

            if query:
                slug_query = slugify(query)
                if slug_query:
                    objects = objects.filter(slug__icontains=slug_query)

            if is_visible is not None:
                objects = objects.filter(is_visible=is_visible)

            objects = objects.order_by("name")

            if page and page_size:
                skip = (page - 1) * page_size
                objects = objects.skip(skip).limit(page_size)

            for menu_model in objects:
                menu_model = self._ensure_slug(menu_model)
                menus.append(MenuInDB.model_validate(menu_model))

            return menus

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"Menus not found")

    async def delete_by_id(self, id: str) -> MenuInDB:
        try:
            menu_model: MenuModel = MenuModel.objects(
                id=id, is_active=True, organization_id=self.organization_id
            ).first()
            menu_model.delete()

            return MenuInDB.model_validate(menu_model)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Menu #{id} not found")
