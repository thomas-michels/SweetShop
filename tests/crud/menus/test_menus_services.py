import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from mongoengine import connect, disconnect
import mongomock

from app.crud.menus.repositories import MenuRepository
from app.crud.menus.schemas import Menu, MenuInDB, UpdateMenu
from app.crud.menus.services import MenuServices
from app.api.exceptions.authentication_exceptions import UnauthorizedException
from app.core.exceptions import NotFoundError
from app.core.utils.utc_datetime import UTCDateTime


class TestMenuServices(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        repo = MenuRepository(organization_id="org1")
        self.service = MenuServices(menu_repository=repo)

    def tearDown(self):
        disconnect()

    async def _menu(self, name="Menu"):
        return Menu(name=name, description="desc")

    @patch("app.crud.menus.services.get_plan_feature", new_callable=AsyncMock)
    async def test_create_menu_unauthorized(self, mock_plan):
        mock_plan.return_value = SimpleNamespace(value="false")
        with self.assertRaises(UnauthorizedException):
            await self.service.create(await self._menu())

    @patch("app.crud.menus.services.get_plan_feature", new_callable=AsyncMock)
    async def test_create_menu_success(self, mock_plan):
        mock_plan.return_value = SimpleNamespace(value="true")
        result = await self.service.create(await self._menu(name="New"))
        self.assertEqual(result.name, "New")

    async def _create_menu_in_db(self, name="Menu"):
        repo = self.service._MenuServices__menu_repository
        return await repo.create(await self._menu(name=name))

    async def test_update_menu(self):
        created = await self._create_menu_in_db(name="Old")
        updated = await self.service.update(id=created.id, updated_menu=UpdateMenu(name="New"))
        self.assertEqual(updated.name, "New")

    async def test_update_menu_without_real_change(self):
        menu = MenuInDB(
            id="1", name="Same", description="d", organization_id="org1",
            created_at=UTCDateTime.now(), updated_at=UTCDateTime.now(), is_active=True
        )
        menu.validate_updated_fields = lambda upd: False
        mock_repo = AsyncMock()
        mock_repo.select_by_id.return_value = menu
        service = MenuServices(menu_repository=mock_repo)
        result = await service.update(id="1", updated_menu=UpdateMenu(name="Same"))
        self.assertEqual(result.name, "Same")
        mock_repo.update.assert_not_awaited()

    async def test_search_all(self):
        mock_repo = AsyncMock()
        mock_repo.select_all.return_value = ["menu"]
        service = MenuServices(menu_repository=mock_repo)
        result = await service.search_all(query=None)
        self.assertEqual(result, ["menu"])
        mock_repo.select_all.assert_awaited()

    async def test_search_count(self):
        mock_repo = AsyncMock()
        mock_repo.select_count.return_value = 3
        service = MenuServices(menu_repository=mock_repo)
        count = await service.search_count(query="a")
        self.assertEqual(count, 3)
        mock_repo.select_count.assert_awaited_with(query="a", is_visible=None)

    async def test_delete_by_id(self):
        mock_repo = AsyncMock()
        mock_repo.delete_by_id.return_value = "deleted"
        service = MenuServices(menu_repository=mock_repo)
        result = await service.delete_by_id(id="d")
        self.assertEqual(result, "deleted")
        mock_repo.delete_by_id.assert_awaited_with(id="d")

    async def test_delete_by_id_not_found(self):
        mock_repo = AsyncMock()
        mock_repo.delete_by_id.side_effect = NotFoundError("nf")
        service = MenuServices(menu_repository=mock_repo)
        with self.assertRaises(NotFoundError):
            await service.delete_by_id(id="x")

    async def test_search_by_id_calls_repo(self):
        mock_repo = AsyncMock()
        mock_repo.select_by_id.return_value = "menu"
        service = MenuServices(menu_repository=mock_repo)
        result = await service.search_by_id(id="m1")
        self.assertEqual(result, "menu")
        mock_repo.select_by_id.assert_awaited_with(id="m1")

    async def test_search_count_with_visibility(self):
        mock_repo = AsyncMock()
        mock_repo.select_count.return_value = 2
        service = MenuServices(menu_repository=mock_repo)
        count = await service.search_count(is_visible=True)
        self.assertEqual(count, 2)
        mock_repo.select_count.assert_awaited_with(query=None, is_visible=True)

    async def test_search_all_with_visibility_and_pagination(self):
        mock_repo = AsyncMock()
        mock_repo.select_all.return_value = ["menu"]
        service = MenuServices(menu_repository=mock_repo)
        result = await service.search_all(query="a", is_visible=False, page=2, page_size=1)
        self.assertEqual(result, ["menu"])
        mock_repo.select_all.assert_awaited_with(query="a", is_visible=False, page=2, page_size=1)
