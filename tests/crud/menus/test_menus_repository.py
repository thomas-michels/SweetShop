import unittest
from mongoengine import connect, disconnect
import mongomock

from app.crud.menus.models import MenuModel
from app.crud.menus.repositories import MenuRepository
from app.crud.menus.schemas import Menu
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.utils.utc_datetime import UTCDateTime


class TestMenuRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        self.repo = MenuRepository(organization_id="org1")

    def tearDown(self):
        disconnect()

    async def _menu(self, name="Menu"):
        return Menu(name=name, description="desc")

    async def test_create_menu(self):
        menu = await self._menu(name="Lunch")
        result = await self.repo.create(menu)
        self.assertEqual(result.name, "Lunch")
        self.assertEqual(result.slug, "lunch")
        self.assertEqual(MenuModel.objects.count(), 1)

    async def test_create_duplicate_menu_raises_error(self):
        menu = await self._menu(name="Lunch")
        await self.repo.create(menu)
        with self.assertRaises(UnprocessableEntity):
            await self.repo.create(menu)

    async def test_create_menu_generates_slug_without_special_characters(self):
        menu = await self._menu(name="Café da Manhã!")
        result = await self.repo.create(menu)

        self.assertEqual(result.name, "Café Da Manhã!")
        self.assertEqual(result.slug, "cafe-da-manha")

    async def test_update_menu(self):
        created = await self.repo.create(await self._menu(name="Old"))
        created.name = "New"
        updated = await self.repo.update(created)
        self.assertEqual(updated.name, "New")
        self.assertEqual(updated.slug, "new")

    async def test_update_menu_not_unique(self):
        first = await self.repo.create(await self._menu(name="A"))
        await self.repo.create(await self._menu(name="B"))
        first.name = "B"
        with self.assertRaises(UnprocessableEntity):
            await self.repo.update(first)

    async def test_select_by_id_success(self):
        created = await self.repo.create(await self._menu())
        result = await self.repo.select_by_id(id=created.id)
        self.assertEqual(result.id, created.id)

    async def test_select_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.select_by_id(id="missing")

    async def test_select_by_name_success(self):
        created = await self.repo.create(await self._menu(name="Sweet"))
        result = await self.repo.select_by_name(name="Sweet")
        self.assertEqual(result.id, created.id)
        self.assertEqual(result.slug, "sweet")

    async def test_select_by_name_uses_slug(self):
        created = await self.repo.create(await self._menu(name="Crème Brûlée"))
        result = await self.repo.select_by_name(name="creme brulee")

        self.assertEqual(result.id, created.id)
        self.assertEqual(result.slug, "creme-brulee")

    async def test_select_by_name_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.select_by_name(name="Ghost")

    async def test_select_by_name_backfills_slug_for_legacy_menu(self):
        legacy_menu = MenuModel(
            organization_id="org1",
            name="Legacy Menu",
            description="desc",
            is_visible=True,
        )
        legacy_menu.save()
        MenuModel.objects(id=legacy_menu.id).update(unset__slug=1)

        result = await self.repo.select_by_name(name="Legacy Menu")

        self.assertEqual(result.slug, "legacy-menu")
        stored_menu = MenuModel.objects(id=legacy_menu.id).first()
        self.assertEqual(stored_menu.slug, "legacy-menu")

    async def test_select_count_with_query(self):
        await self.repo.create(await self._menu(name="Café da Manhã"))
        await self.repo.create(await self._menu(name="Cafe Especial"))
        await self.repo.create(await self._menu(name="Suco"))
        count = await self.repo.select_count(query="Cafe")
        self.assertEqual(count, 2)

    async def test_select_count_supports_legacy_menu_without_slug(self):
        legacy_menu = MenuModel(
            organization_id="org1",
            name="Café Antigo",
            description="desc",
            is_visible=True,
        )
        legacy_menu.save()
        MenuModel.objects(id=legacy_menu.id).update(unset__slug=1)

        count = await self.repo.select_count(query="Cafe")

        self.assertEqual(count, 1)
        stored_menu = MenuModel.objects(id=legacy_menu.id).first()
        self.assertEqual(stored_menu.slug, "cafe-antigo")

    async def test_select_all_with_pagination(self):
        await self.repo.create(await self._menu(name="A"))
        await self.repo.create(await self._menu(name="B"))
        await self.repo.create(await self._menu(name="C"))
        results = await self.repo.select_all(query=None, page=1, page_size=2)
        self.assertEqual(len(results), 2)
        results_p2 = await self.repo.select_all(query=None, page=2, page_size=2)
        self.assertEqual(len(results_p2), 1)
        names = {r.name for r in results + results_p2}
        self.assertEqual(names, {"A", "B", "C"})

    async def test_select_all_returns_slug_for_legacy_menu(self):
        legacy_menu = MenuModel(
            organization_id="org1",
            name="Menu Sem Slug",
            description="desc",
            is_visible=True,
        )
        legacy_menu.save()
        MenuModel.objects(id=legacy_menu.id).update(unset__slug=1)

        results = await self.repo.select_all(query=None)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].slug, "menu-sem-slug")

    async def test_delete_by_id_success(self):
        created = await self.repo.create(await self._menu(name="Del"))
        result = await self.repo.delete_by_id(id=created.id)
        self.assertEqual(MenuModel.objects(is_active=True).count(), 0)
        self.assertEqual(result.name, "Del")

    async def test_delete_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.delete_by_id(id="missing")

    async def test_update_nonexistent_menu_raises_unprocessable(self):
        from app.crud.menus.schemas import MenuInDB
        missing = MenuInDB(
            id="missing",
            name="Missing",
            description="d",
            organization_id="org1",
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
            is_active=True,
            slug="missing",
        )
        with self.assertRaises(UnprocessableEntity):
            await self.repo.update(missing)

    async def test_create_menu_title_cases_name(self):
        menu = await self._menu(name="mY meNu")
        result = await self.repo.create(menu)
        self.assertEqual(result.name, "My Menu")
        self.assertEqual(result.slug, "my-menu")

    async def test_select_by_id_raise_false_returns_none(self):
        result = await self.repo.select_by_id(id="missing", raise_404=False)
        self.assertIsNone(result)

    async def test_select_by_name_raise_false_returns_none(self):
        result = await self.repo.select_by_name(name="ghost", raise_404=False)
        self.assertIsNone(result)

    async def test_select_count_filter_is_visible(self):
        visible = await self.repo.create(await self._menu(name="Visible"))
        hidden = await self.repo.create(await self._menu(name="Hidden"))

        MenuModel.objects(id=visible.id).update(is_visible=True)

        count_visible = await self.repo.select_count(query=None, is_visible=True)
        count_hidden = await self.repo.select_count(query=None, is_visible=False)

        self.assertEqual(count_visible, 1)
        self.assertEqual(count_hidden, 1)

    async def test_select_all_filter_is_visible_and_query(self):
        visible = await self.repo.create(await self._menu(name="Apple"))
        hidden = await self.repo.create(await self._menu(name="Banana"))
        MenuModel.objects(id=visible.id).update(is_visible=True)

        results = await self.repo.select_all(query="Ap", is_visible=True)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Apple")

        hidden_results = await self.repo.select_all(query=None, is_visible=False)

        self.assertEqual(len(hidden_results), 1)
        self.assertEqual(hidden_results[0].name, "Banana")
