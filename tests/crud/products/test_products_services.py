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
from app.crud.section_items.repositories import SectionItemRepository
from app.crud.section_items.schemas import SectionItem, ItemType
from app.crud.section_items.models import SectionItemModel
from app.crud.offers.repositories import OfferRepository
from app.crud.offers.schemas import Offer, OfferProduct
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
        self.section_item_repo = SectionItemRepository(organization_id="org1")
        self.service = ProductServices(
            product_repository=repo,
            tag_repository=self.tag_repo,
            file_repository=self.file_repo,
            additional_services=self.additional_repo,
            section_item_repository=self.section_item_repo,
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
        service = ProductServices(
            product_repository=mock_repo,
            tag_repository=AsyncMock(),
            file_repository=AsyncMock(),
            additional_services=AsyncMock(),
            section_item_repository=AsyncMock(),
        )
        result = await service.update(id="1", updated_product=UpdateProduct())
        self.assertEqual(result.name, "Same")
        mock_repo.update.assert_not_awaited()

    async def test_search_by_id_calls_repo(self):
        mock_repo = AsyncMock()
        mock_repo.select_by_id.return_value = "prod"
        service = ProductServices(
            product_repository=mock_repo,
            tag_repository=AsyncMock(),
            file_repository=AsyncMock(),
            additional_services=AsyncMock(),
            section_item_repository=AsyncMock(),
        )
        result = await service.search_by_id(id="x")
        self.assertEqual(result, "prod")
        mock_repo.select_by_id.assert_awaited_with(id="x")

    async def test_search_all(self):
        mock_repo = AsyncMock()
        mock_repo.select_all.return_value = ["prod"]
        service = ProductServices(
            product_repository=mock_repo,
            tag_repository=AsyncMock(),
            file_repository=AsyncMock(),
            additional_services=AsyncMock(),
            section_item_repository=AsyncMock(),
        )
        result = await service.search_all(query=None)
        self.assertEqual(result, ["prod"])
        mock_repo.select_all.assert_awaited()

    async def test_search_count(self):
        mock_repo = AsyncMock()
        mock_repo.select_count.return_value = 3
        service = ProductServices(
            product_repository=mock_repo,
            tag_repository=AsyncMock(),
            file_repository=AsyncMock(),
            additional_services=AsyncMock(),
            section_item_repository=AsyncMock(),
        )
        count = await service.search_count(query="a")
        self.assertEqual(count, 3)
        mock_repo.select_count.assert_awaited_with(query="a", tags=[])

    async def test_delete_by_id(self):
        mock_repo = AsyncMock()
        mock_repo.delete_by_id.return_value = "deleted"
        additional = AsyncMock()
        section_repo = AsyncMock()
        service = ProductServices(
            product_repository=mock_repo,
            tag_repository=AsyncMock(),
            file_repository=AsyncMock(),
            additional_services=additional,
            section_item_repository=section_repo,
        )
        result = await service.delete_by_id(id="d")
        self.assertEqual(result, "deleted")
        mock_repo.delete_by_id.assert_awaited_with(id="d")
        additional.delete_by_product_id.assert_awaited_with(product_id="d")
        section_repo.delete_by_item_id.assert_awaited_with(
            item_id="d", item_type=ItemType.PRODUCT
        )


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

    @patch("app.crud.products.services.get_plan_feature", new_callable=AsyncMock)
    async def test_delete_product_removes_section_items(self, mock_plan):
        mock_plan.return_value = SimpleNamespace(value="-")
        product = await self.service.create(await self._product())
        section_item = SectionItem(
            section_id="sec1",
            item_id=product.id,
            item_type=ItemType.PRODUCT,
            position=1,
            is_visible=True,
        )
        await self.section_item_repo.create(section_item)
        self.assertEqual(
            SectionItemModel.objects(is_active=True).count(), 1
        )
        await self.service.delete_by_id(id=product.id)
        self.assertEqual(
            SectionItemModel.objects(is_active=True).count(), 0
        )

    @patch("app.crud.products.services.get_plan_feature", new_callable=AsyncMock)
    async def test_delete_product_removes_from_offers(self, mock_plan):
        mock_plan.return_value = SimpleNamespace(value="-")
        prod1 = await self.service.create(await self._product(name="P1"))
        prod2 = await self.service.create(await self._product(name="P2"))
        offer_repo = OfferRepository(organization_id="org1")
        offer = Offer(
            name="Combo",
            description="d",
            products=[
                OfferProduct(
                    product_id=prod1.id,
                    name=prod1.name,
                    description=prod1.description,
                    unit_cost=prod1.unit_cost,
                    unit_price=prod1.unit_price,
                    quantity=1,
                    file_id=None,
                ),
                OfferProduct(
                    product_id=prod2.id,
                    name=prod2.name,
                    description=prod2.description,
                    unit_cost=prod2.unit_cost,
                    unit_price=prod2.unit_price,
                    quantity=1,
                    file_id=None,
                ),
            ],
            unit_cost=prod1.unit_cost + prod2.unit_cost,
            unit_price=prod1.unit_price + prod2.unit_price,
            starts_at=None,
            ends_at=None,
            file_id=None,
            is_visible=True,
        )
        offer_in_db = await offer_repo.create(offer)
        await self.service.delete_by_id(id=prod1.id)
        updated_offer = await offer_repo.select_by_id(id=offer_in_db.id)
        self.assertEqual(len(updated_offer.products), 1)
        self.assertEqual(updated_offer.products[0].product_id, prod2.id)
        self.assertEqual(updated_offer.unit_cost, prod2.unit_cost)
        self.assertEqual(updated_offer.unit_price, prod2.unit_price)

    async def test_search_all_expand_file_uses_batch(self):
        prod_repo = AsyncMock()
        prod_repo.select_all.return_value = [
            ProductInDB(
                id="p1",
                name="P1",
                description="d",
                unit_price=1.0,
                unit_cost=1.0,
                tags=[],
                file_id="f1",
                organization_id="org1",
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
                is_active=True,
            ),
            ProductInDB(
                id="p2",
                name="P2",
                description="d",
                unit_price=1.0,
                unit_cost=1.0,
                tags=[],
                file_id="f2",
                organization_id="org1",
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
                is_active=True,
            ),
        ]
        file_repo = AsyncMock()
        file_repo.select_by_ids.return_value = {"f1": "file1", "f2": "file2"}
        service = ProductServices(
            product_repository=prod_repo,
            tag_repository=AsyncMock(),
            file_repository=file_repo,
            additional_services=AsyncMock(),
            section_item_repository=AsyncMock(),
        )
        result = await service.search_all(query=None, expand=["file"])
        file_repo.select_by_ids.assert_awaited_once_with(["f1", "f2"])
        self.assertEqual(result[0].file, "file1")
        self.assertEqual(result[1].file, "file2")
