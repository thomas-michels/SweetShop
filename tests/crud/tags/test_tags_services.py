import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from mongoengine import connect, disconnect
import mongomock

from app.crud.tags.repositories import TagRepository
from app.crud.tags.schemas import Tag, TagInDB, UpdateTag
from app.crud.tags.services import TagServices
from app.api.exceptions.authentication_exceptions import UnauthorizedException


class TestTagServices(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default"
        )
        repo = TagRepository(organization_id="org1")
        self.service = TagServices(tag_repository=repo)

    def tearDown(self):
        disconnect()

    @patch("app.crud.tags.services.get_plan_feature", new_callable=AsyncMock)
    async def test_create_tag_respects_plan_limit(self, mock_plan):
        mock_plan.return_value = SimpleNamespace(value="2")
        await self.service.create(Tag(name="First"))

        with self.assertRaises(UnauthorizedException):
            await self.service.create(Tag(name="Second"))

    @patch("app.crud.tags.services.get_plan_feature", new_callable=AsyncMock)
    async def test_create_tag_success(self, mock_plan):
        mock_plan.return_value = SimpleNamespace(value="-")

        result = await self.service.create(Tag(name="Sample"))

        self.assertEqual(result.name, "Sample")

    async def test_create_tag_within_plan_limit(self):
        mock_repo = AsyncMock()
        mock_repo.select_count.return_value = 0
        mock_repo.create.return_value = TagInDB(id="123", name="Limited", organization_id="org1")

        service = TagServices(tag_repository=mock_repo)

        with patch("app.crud.tags.services.get_plan_feature", new_callable=AsyncMock) as mock_feature:
            mock_feature.return_value = SimpleNamespace(value="2")
            result = await service.create(Tag(name="Limited"))
            self.assertEqual(result.name, "Limited")

    @patch("app.crud.tags.services.get_plan_feature", new_callable=AsyncMock)
    async def test_update_tag(self, mock_plan):
        mock_plan.return_value = SimpleNamespace(value="-")
        created = await self.service.create(Tag(name="Old"))

        updated = await self.service.update(id=created.id, updated_tag=UpdateTag(name="New"))

        self.assertEqual(updated.name, "New")

    async def test_update_tag_with_real_change(self):
        tag = TagInDB(id="id1", name="Old", organization_id="org1")
        tag.validate_updated_fields = lambda update_tag: True

        mock_repo = AsyncMock()
        mock_repo.select_by_id.return_value = tag
        mock_repo.update.return_value = TagInDB(id="id1", name="Updated", organization_id="org1")

        service = TagServices(tag_repository=mock_repo)
        result = await service.update(id="id1", updated_tag=UpdateTag(name="Updated"))
        self.assertEqual(result.name, "Updated")

    async def test_update_tag_without_real_change(self):
        tag = TagInDB(id="id1", name="Same", organization_id="org1")
        tag.validate_updated_fields = lambda update_tag: False

        mock_repo = AsyncMock()
        mock_repo.select_by_id.return_value = tag

        service = TagServices(tag_repository=mock_repo)
        result = await service.update(id="id1", updated_tag=UpdateTag(name="Same"))
        self.assertEqual(result.name, "Same")
        mock_repo.update.assert_not_awaited()

    async def test_search_by_id_calls_repo(self):
        tag = TagInDB(id="x", name="Any", organization_id="org1")
        mock_repo = AsyncMock()
        mock_repo.select_by_id.return_value = tag

        service = TagServices(tag_repository=mock_repo)

        result = await service.search_by_id(id="x")

        self.assertEqual(result, tag)
        mock_repo.select_by_id.assert_awaited_with(id="x")

    async def test_search_all(self):
        mock_repo = AsyncMock()
        mock_repo.select_all.return_value = [TagInDB(id="1", name="A", organization_id="org1")]

        service = TagServices(tag_repository=mock_repo)

        result = await service.search_all(query=None, page=1, page_size=10)

        self.assertEqual(len(result), 1)
        mock_repo.select_all.assert_awaited()

    async def test_count_all(self):
        mock_repo = AsyncMock()
        mock_repo.select_count.return_value = 5

        service = TagServices(tag_repository=mock_repo)

        count = await service.count_all(query="a")

        self.assertEqual(count, 5)
        mock_repo.select_count.assert_awaited_with(query="a")

    async def test_delete_by_id(self):
        tag = TagInDB(id="d", name="Del", organization_id="org1")
        mock_repo = AsyncMock()
        mock_repo.delete_by_id.return_value = tag

        service = TagServices(tag_repository=mock_repo)

        result = await service.delete_by_id(id="d")

        self.assertEqual(result, tag)
        mock_repo.delete_by_id.assert_awaited_with(id="d")
