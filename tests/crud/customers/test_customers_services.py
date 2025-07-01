import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from mongoengine import connect, disconnect
import mongomock

from app.crud.customers.repositories import CustomerRepository
from app.crud.customers.schemas import Customer, CustomerInDB, UpdateCustomer
from app.crud.customers.services import CustomerServices
from app.core.utils.utc_datetime import UTCDateTime
from app.api.exceptions.authentication_exceptions import UnauthorizedException


class TestCustomerServices(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        repo = CustomerRepository(organization_id="org1")
        tag_repo = AsyncMock()
        self.service = CustomerServices(customer_repository=repo, tag_repository=tag_repo)

    def tearDown(self):
        disconnect()

    async def _customer(self, name="John"):
        return Customer(name=name)

    @patch("app.crud.customers.services.get_plan_feature", new_callable=AsyncMock)
    async def test_create_customer_respects_plan_limit(self, mock_plan):
        mock_plan.return_value = SimpleNamespace(value="2")
        await self.service.create(await self._customer())
        with self.assertRaises(UnauthorizedException):
            await self.service.create(await self._customer(name="Another"))

    @patch("app.crud.customers.services.get_plan_feature", new_callable=AsyncMock)
    async def test_create_customer_success(self, mock_plan):
        mock_plan.return_value = SimpleNamespace(value="-")
        result = await self.service.create(await self._customer())
        self.assertEqual(result.name, "John")

    @patch("app.crud.customers.services.get_plan_feature", new_callable=AsyncMock)
    async def test_update_customer(self, mock_plan):
        mock_plan.return_value = SimpleNamespace(value="-")
        created = await self.service.create(await self._customer())
        updated = await self.service.update(id=created.id, updated_customer=UpdateCustomer(name="New"))
        self.assertEqual(updated.name, "New")

    async def test_update_without_real_change(self):
        mock_repo = AsyncMock()
        mock_repo.select_by_id.return_value = CustomerInDB(
            id="1", name="Same", organization_id="org1", is_active=True,
            addresses=[], tags=[],
            created_at=UTCDateTime.now(), updated_at=UTCDateTime.now()
        )
        mock_repo.update.return_value = mock_repo.select_by_id.return_value
        service = CustomerServices(customer_repository=mock_repo, tag_repository=AsyncMock())
        result = await service.update(id="1", updated_customer=UpdateCustomer())
        self.assertEqual(result.name, "Same")
        mock_repo.update.assert_not_awaited()

    async def test_search_by_id_calls_repo(self):
        mock_repo = AsyncMock()
        mock_repo.select_by_id.return_value = CustomerInDB(
            id="x", name="Cust", organization_id="org1", is_active=True,
            addresses=[], tags=[], created_at=UTCDateTime.now(), updated_at=UTCDateTime.now()
        )
        service = CustomerServices(customer_repository=mock_repo, tag_repository=AsyncMock())
        result = await service.search_by_id(id="x")
        self.assertEqual(result.id, "x")
        mock_repo.select_by_id.assert_awaited_with(id="x")

    async def test_search_all(self):
        mock_repo = AsyncMock()
        mock_repo.select_all.return_value = [
            CustomerInDB(
                id="1", name="A", organization_id="org1", is_active=True,
                addresses=[], tags=[], created_at=UTCDateTime.now(), updated_at=UTCDateTime.now()
            )
        ]
        service = CustomerServices(customer_repository=mock_repo, tag_repository=AsyncMock())
        result = await service.search_all(query=None)
        self.assertEqual(len(result), 1)
        mock_repo.select_all.assert_awaited()

    async def test_search_count(self):
        mock_repo = AsyncMock()
        mock_repo.select_count.return_value = 5
        service = CustomerServices(customer_repository=mock_repo, tag_repository=AsyncMock())
        count = await service.search_count(query="a")
        self.assertEqual(count, 5)
        mock_repo.select_count.assert_awaited_with(query="a", tags=[])

    async def test_delete_by_id(self):
        mock_repo = AsyncMock()
        mock_repo.delete_by_id.return_value = CustomerInDB(
            id="d", name="Del", organization_id="org1", is_active=True,
            addresses=[], tags=[], created_at=UTCDateTime.now(), updated_at=UTCDateTime.now()
        )
        service = CustomerServices(customer_repository=mock_repo, tag_repository=AsyncMock())
        result = await service.delete_by_id(id="d")
        self.assertEqual(result.id, "d")
        mock_repo.delete_by_id.assert_awaited_with(id="d")

    async def test_search_all_expand_tags(self):
        from app.crud.tags.schemas import TagInDB
        mock_repo = AsyncMock()
        mock_repo.select_all.return_value = [
            CustomerInDB(
                id="1", name="A", organization_id="org1", is_active=True,
                addresses=[], tags=["tag1"],
                created_at=UTCDateTime.now(), updated_at=UTCDateTime.now()
            )
        ]
        mock_tag_repo = AsyncMock()
        mock_tag_repo.select_by_id.return_value = TagInDB(id="tag1", name="Tag 1", organization_id="org1")
        service = CustomerServices(customer_repository=mock_repo, tag_repository=mock_tag_repo)
        result = await service.search_all(query=None, expand=["tags"])
        self.assertEqual(result[0].tags[0].name, "Tag 1")
        mock_tag_repo.select_by_id.assert_awaited_with(id="tag1", raise_404=False)

    @patch("app.crud.customers.services.get_plan_feature", new_callable=AsyncMock)
    async def test_create_customer_validates_tags(self, mock_plan):
        mock_plan.return_value = SimpleNamespace(value="-")
        mock_tag_repo = AsyncMock()
        service = CustomerServices(customer_repository=self.service._CustomerServices__repository, tag_repository=mock_tag_repo)
        customer = await self._customer(name="Tagged")
        customer.tags = ["t1", "t2"]
        await service.create(customer)
        mock_tag_repo.select_by_id.assert_any_await(id="t1")
        mock_tag_repo.select_by_id.assert_any_await(id="t2")

    async def test_search_all_expand_tags_cache(self):
        from app.crud.tags.schemas import TagInDB
        mock_repo = AsyncMock()
        mock_repo.select_all.return_value = [
            CustomerInDB(
                id="1", name="A", organization_id="org1", is_active=True,
                addresses=[], tags=["tag1"],
                created_at=UTCDateTime.now(), updated_at=UTCDateTime.now()
            ),
            CustomerInDB(
                id="2", name="B", organization_id="org1", is_active=True,
                addresses=[], tags=["tag1"],
                created_at=UTCDateTime.now(), updated_at=UTCDateTime.now()
            )
        ]
        mock_tag_repo = AsyncMock()
        mock_tag_repo.select_by_id.return_value = TagInDB(id="tag1", name="Tag 1", organization_id="org1")
        service = CustomerServices(customer_repository=mock_repo, tag_repository=mock_tag_repo)
        result = await service.search_all(query=None, expand=["tags"])
        self.assertEqual(len(result), 2)
        self.assertEqual(mock_tag_repo.select_by_id.await_count, 1)
