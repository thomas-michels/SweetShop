import unittest
from mongoengine import connect, disconnect
import mongomock

from app.crud.tags.models import TagModel
from app.crud.tags.repositories import TagRepository
from app.crud.tags.schemas import Tag
from app.core.exceptions import NotFoundError, UnprocessableEntity


class TestTagRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default"
        )
        self.repo = TagRepository(organization_id="org1")

    def tearDown(self):
        disconnect()

    async def test_create_tag(self):
        tag = Tag(name="Street Mode")

        result = await self.repo.create(tag)

        self.assertEqual(result.name, "Street Mode")
        self.assertEqual(TagModel.objects.count(), 1)

    async def test_create_duplicate_tag_raises_error(self):
        tag = Tag(name="Summer")
        await self.repo.create(tag)

        with self.assertRaises(UnprocessableEntity):
            await self.repo.create(tag)

    async def test_create_tag_with_whitespace_and_lowercase(self):
        tag = Tag(name="  new tag  ")
        result = await self.repo.create(tag)
        self.assertEqual(result.name, "New Tag")

    async def test_update_tag_name(self):
        tag = Tag(name="Winter")
        created = await self.repo.create(tag)

        created.name = "Autumn"
        updated = await self.repo.update(created)

        self.assertEqual(updated.name, "Autumn")

    async def test_select_by_id_success(self):
        created = await self.repo.create(Tag(name="UniqueTag"))
        result = await self.repo.select_by_id(id=created.id)
        self.assertEqual(result.name, "Uniquetag")

    async def test_select_by_id_with_invalid_id_and_raise_404_false(self):
        result = await self.repo.select_by_id(id="invalid_id", raise_404=False)
        self.assertIsNone(result)

    async def test_select_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.select_by_id(id="missing")

    async def test_select_by_name_returns_none(self):
        result = await self.repo.select_by_name(name="Ghost")

        self.assertIsNone(result)

    async def test_select_by_name_existing_tag(self):
        await self.repo.create(Tag(name="Exists"))
        result = await self.repo.select_by_name(name="exists")
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "Exists")

    async def test_select_count_with_query(self):
        await self.repo.create(Tag(name="Spring"))
        await self.repo.create(Tag(name="Summer"))
        await self.repo.create(Tag(name="Spring Time"))

        count = await self.repo.select_count(query="Spring")

        self.assertEqual(count, 2)

    async def test_select_count_without_query(self):
        await self.repo.create(Tag(name="Tag1"))
        await self.repo.create(Tag(name="Tag2"))
        count = await self.repo.select_count()
        self.assertEqual(count, 2)

    async def test_select_all_with_pagination(self):
        await self.repo.create(Tag(name="Apple"))
        await self.repo.create(Tag(name="Banana"))
        await self.repo.create(Tag(name="Cherry"))

        results = await self.repo.select_all(query=None, page=1, page_size=2)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].name, "Apple")

        results_page_2 = await self.repo.select_all(query=None, page=2, page_size=2)

        self.assertEqual(len(results_page_2), 1)
        self.assertEqual(results_page_2[0].name, "Cherry")

    async def test_select_all_with_query(self):
        await self.repo.create(Tag(name="Test Tag A"))
        await self.repo.create(Tag(name="Tag B"))
        await self.repo.create(Tag(name="Test Tag C"))

        results = await self.repo.select_all(query="Test", page=1, page_size=10)
        self.assertEqual(len(results), 2)
        self.assertTrue(all("Test" in tag.name for tag in results))

    async def test_delete_by_id_success(self):
        created = await self.repo.create(Tag(name="Temporary"))

        result = await self.repo.delete_by_id(id=created.id)

        self.assertEqual(TagModel.objects(is_active=True).count(), 0)
        self.assertEqual(result.name, "Temporary")

    async def test_delete_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.delete_by_id(id="missing")

    async def test_update_tag_not_unique(self):
        first = await self.repo.create(Tag(name="Alpha"))
        await self.repo.create(Tag(name="Beta"))

        first.name = "Beta"

        with self.assertRaises(UnprocessableEntity):
            await self.repo.update(first)
