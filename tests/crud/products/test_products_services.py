import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from mongoengine import connect, disconnect
import mongomock

from app.crud.products.repositories import ProductRepository
from app.crud.products.schemas import Product, ProductInDB, UpdateProduct
from app.crud.products.services import ProductServices
from app.crud.tags.repositories import TagRepository
from app.crud.files.repositories import FileRepository
from app.core.utils.utc_datetime import UTCDateTime
from app.api.exceptions.authentication_exceptions import UnauthorizedException, BadRequestException


class TestProductServices(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        repo = ProductRepository(organization_id="org1")
        self.tag_repo = TagRepository(organization_id="org1")
        self.file_repo = FileRepository(organization_id="org1")
        self.additional_repo = AsyncMock()
        self.service = ProductServices(
            product_repository=repo,
            tag_repository=self.tag_repo,
            file_repository=self.file_repo,
            additional_services=self.additional_repo,
        )

    def tearDown(self):
        disconnect()

    async def _product(self, name="Cake"):
        return Product(
            name=name,
            description="desc",
            unit_price=10.0,
            unit_cost=5.0,
            tags=[],
        )

    @patch("app.crud.products.services.get_plan_feature", new_callable=AsyncMock)
    async def test_create_product_respects_plan_limit(self, mock_plan):
        mock_plan.return_value = SimpleNamespace(value="2")
        await self.service.create(await self._product())
        with self.assertRaises(UnauthorizedException):
            await self.service.create(await self._product(name="Another"))

    @patch("app.crud.products.services.get_plan_feature", new_callable=AsyncMock)
    async def test_create_product_success(self, mock_plan):
        mock_plan.return_value = SimpleNamespace(value="-")
        result = await self.service.create(await self._product())
        self.assertEqual(result.name, "Cake")

    @patch("app.crud.products.services.get_plan_feature", new_callable=AsyncMock)
    async def test_create_product_invalid_file(self, mock_plan):
        mock_plan.return_value = SimpleNamespace(value="-")
        prod = await self._product()
        prod.file_id = "file1"
        self.file_repo.select_by_id = AsyncMock(return_value=SimpleNamespace(purpose="OTHER"))
        with self.assertRaises(BadRequestException):
            await self.service.create(prod)

    @patch("app.crud.products.services.get_plan_feature", new_callable=AsyncMock)
    async def test_update_product(self, mock_plan):
        mock_plan.return_value = SimpleNamespace(value="-")
        created = await self.service.create(await self._product())
        updated = await self.service.update(id=created.id, updated_product=UpdateProduct(name="New"))
        self.assertEqual(updated.name, "New")

    async def test_update_without_real_change(self):
        prod = ProductInDB(
            id="1",
            name="Same",
            description="d",
            unit_price=1.0,
            unit_cost=1.0,
            tags=[],
            organization_id="org1",
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
            is_active=True,
        )
        prod.validate_updated_fields = lambda update_product: False
        mock_repo = AsyncMock()
        mock_repo.select_by_id.return_value = prod
        service = ProductServices(product_repository=mock_repo, tag_repository=AsyncMock(), file_repository=AsyncMock(), additional_services=AsyncMock())
        result = await service.update(id="1", updated_product=UpdateProduct())
        self.assertEqual(result.name, "Same")
        mock_repo.update.assert_not_awaited()

    async def test_search_by_id_calls_repo(self):
        mock_repo = AsyncMock()
        mock_repo.select_by_id.return_value = "prod"
        service = ProductServices(product_repository=mock_repo, tag_repository=AsyncMock(), file_repository=AsyncMock(), additional_services=AsyncMock())
        result = await service.search_by_id(id="x")
        self.assertEqual(result, "prod")
        mock_repo.select_by_id.assert_awaited_with(id="x")

    async def test_search_all(self):
        mock_repo = AsyncMock()
        mock_repo.select_all.return_value = ["prod"]
        service = ProductServices(product_repository=mock_repo, tag_repository=AsyncMock(), file_repository=AsyncMock(), additional_services=AsyncMock())
        result = await service.search_all(query=None)
        self.assertEqual(result, ["prod"])
        mock_repo.select_all.assert_awaited()

    async def test_search_count(self):
        mock_repo = AsyncMock()
        mock_repo.select_count.return_value = 3
        service = ProductServices(product_repository=mock_repo, tag_repository=AsyncMock(), file_repository=AsyncMock(), additional_services=AsyncMock())
        count = await service.search_count(query="a")
        self.assertEqual(count, 3)
        mock_repo.select_count.assert_awaited_with(query="a", tags=[])

    async def test_delete_by_id(self):
        mock_repo = AsyncMock()
        mock_repo.delete_by_id.return_value = "deleted"
        additional = AsyncMock()
        service = ProductServices(product_repository=mock_repo, tag_repository=AsyncMock(), file_repository=AsyncMock(), additional_services=additional)
        result = await service.delete_by_id(id="d")
        self.assertEqual(result, "deleted")
        mock_repo.delete_by_id.assert_awaited_with(id="d")
        additional.delete_by_product_id.assert_awaited_with(product_id="d")


    @patch("app.crud.products.services.get_plan_feature", new_callable=AsyncMock)
    async def test_expand_additionals_uses_service(self, mock_plan):
        mock_plan.return_value = SimpleNamespace(value="-")
        created = await self.service.create(await self._product())
        self.additional_repo.search_by_product_id = AsyncMock(return_value=["grp"])
        result = await self.service.search_by_id(id=created.id, expand=["additionals"])
        self.additional_repo.search_by_product_id.assert_awaited_with(
            product_id=created.id
        )
        self.assertEqual(result.additionals, ["grp"])
