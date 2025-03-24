from datetime import datetime
from typing import List
from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository

from .models import MenuModel
from .schemas import Menu, MenuInDB

_logger = get_logger(__name__)


class MenuRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.organization_id = organization_id

    async def create(self, menu: Menu) -> MenuInDB:
        try:
            menu_model = MenuModel(
                created_at=datetime.now(),
                updated_at=datetime.now(),
                organization_id=self.organization_id,
                **menu.model_dump()
            )
            menu_model.name = menu_model.name.title()

            menu_model.save()
            _logger.info(f"Menu {menu.name} saved for organization {self.organization_id}")

            return MenuInDB.model_validate(menu_model)

        except Exception as error:
            _logger.error(f"Error on create_menu: {str(error)}")
            raise UnprocessableEntity(message="Error on create new menu")

    async def update(self, menu: MenuInDB) -> MenuInDB:
        try:
            menu_model: MenuModel = MenuModel.objects(
                id=menu.id,
                is_active=True,
                organization_id=self.organization_id
            ).first()
            menu.name = menu.name.title()

            menu_model.update(**menu.model_dump())

            return await self.select_by_id(id=menu.id)

        except Exception as error:
            _logger.error(f"Error on update_menu: {str(error)}")
            raise UnprocessableEntity(message="Error on update menu")

    async def select_count(self) -> int:
        try:
            count = MenuModel.objects(
                is_active=True,
                organization_id=self.organization_id,
            ).count()

            return count if count else 0

        except Exception as error:
            _logger.error(f"Error on select_count: {str(error)}")
            return 0

    async def select_by_id(self, id: str, raise_404: bool = True) -> MenuInDB:
        try:
            menu_model: MenuModel = MenuModel.objects(
                id=id,
                is_active=True,
                organization_id=self.organization_id
            ).first()

            return MenuInDB.model_validate(menu_model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            if raise_404:
                raise NotFoundError(message=f"Menu #{id} not found")

    async def select_all(self, query: str, is_visible: bool = None) -> List[MenuInDB]:
        try:
            menus = []

            objects = MenuModel.objects(
                is_active=True,
                organization_id=self.organization_id
            )

            if query:
                objects = objects.filter(name__iregex=query)

            if is_visible is not None:
                objects = objects.filter(is_visible=is_visible)

            for menu_model in objects.order_by("created_at"):
                menus.append(MenuInDB.model_validate(menu_model))

            return menus

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"Menus not found")

    async def delete_by_id(self, id: str) -> MenuInDB:
        try:
            menu_model: MenuModel = MenuModel.objects(
                id=id,
                is_active=True,
                organization_id=self.organization_id
            ).first()
            menu_model.delete()

            return MenuInDB.model_validate(menu_model)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Menu #{id} not found")
