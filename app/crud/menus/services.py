from typing import List
from app.api.dependencies.get_plan_feature import get_plan_feature
from app.api.exceptions.authentication_exceptions import UnauthorizedException
from app.core.utils.features import Feature
from .schemas import Menu, MenuInDB, UpdateMenu
from .repositories import MenuRepository


class MenuServices:

    def __init__(
        self,
        menu_repository: MenuRepository,
    ) -> None:
        self.__menu_repository = menu_repository

    async def create(self, menu: Menu) -> MenuInDB:
        plan_feature = await get_plan_feature(
            organization_id=self.__menu_repository.organization_id,
            feature_name=Feature.DISPLAY_MENU
        )

        if not plan_feature or not plan_feature.value.startswith("t"):
            raise UnauthorizedException(detail=f"You cannot access this feature")

        if await self.search_count() > 3:
            raise UnauthorizedException(detail=f"You cannot create more than 3 menus")

        menu_in_db = await self.__menu_repository.create(menu=menu)
        return menu_in_db

    async def update(self, id: str, updated_menu: UpdateMenu) -> MenuInDB:
        menu_in_db = await self.search_by_id(id=id)

        is_updated = menu_in_db.validate_updated_fields(update_menu=updated_menu)

        if is_updated:
            menu_in_db = await self.__menu_repository.update(menu=menu_in_db)

        return menu_in_db

    async def search_count(self) -> int:
        return await self.__menu_repository.select_count()

    async def search_by_id(self, id: str) -> MenuInDB:
        menu_in_db = await self.__menu_repository.select_by_id(id=id)
        return menu_in_db

    async def search_all(self, query: str, is_visible: bool = None, expand: List[str] = []) -> List[MenuInDB]:
        menus = await self.__menu_repository.select_all(
            query=query,
            is_visible=is_visible
        )
        return menus

    async def delete_by_id(self, id: str) -> MenuInDB:
        menu_in_db = await self.__menu_repository.delete_by_id(id=id)
        return menu_in_db
