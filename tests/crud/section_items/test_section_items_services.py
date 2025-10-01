import unittest
from unittest.mock import AsyncMock
from mongoengine import connect, disconnect
import mongomock

from app.crud.section_items.repositories import SectionItemRepository
from app.crud.section_items.schemas import SectionItem, UpdateSectionItem, SectionItemInDB, ItemType
from app.crud.section_items.services import SectionItemServices
from app.core.utils.utc_datetime import UTCDateTime


class TestSectionItemServices(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        repo = SectionItemRepository(organization_id="org1")
        self.section_repo = AsyncMock()
        self.offer_service = AsyncMock()
        self.product_service = AsyncMock()
        self.service = SectionItemServices(
            section_item_repository=repo,
            section_repository=self.section_repo,
            offer_service=self.offer_service,
            product_service=self.product_service,
        )

    def tearDown(self):
        disconnect()

    async def _section_item(self):
        return SectionItem(section_id="sec1", item_id="off1", item_type=ItemType.OFFER, position=1, is_visible=True)

    async def test_create_section_item(self):
        self.section_repo.select_by_id.return_value = None
        self.offer_service.search_by_id.return_value = None
        result = await self.service.create(await self._section_item())
        self.assertIsInstance(result, SectionItemInDB)
        self.section_repo.select_by_id.assert_awaited_with(id="sec1")
        self.offer_service.search_by_id.assert_awaited_with(id="off1")

    async def test_create_section_item_with_product(self):
        self.section_repo.select_by_id.return_value = None
        self.product_service.search_by_id.return_value = None
        so = SectionItem(section_id="sec1", item_id="prod1", item_type=ItemType.PRODUCT, position=1, is_visible=True)
        result = await self.service.create(so)
        self.assertIsInstance(result, SectionItemInDB)
        self.product_service.search_by_id.assert_awaited_with(id="prod1")

    async def test_update_section_item(self):
        self.section_repo.select_by_id.return_value = None
        self.offer_service.search_by_id.return_value = None
        created = await self.service.create(await self._section_item())
        updated = await self.service.update(id=created.id, updated_section_item=UpdateSectionItem(position=2))
        self.assertEqual(updated.position, 2)

    async def test_search_by_id_calls_repo(self):
        mock_repo = AsyncMock()
        mock_repo.select_by_id.return_value = "obj"
        service = SectionItemServices(
            section_item_repository=mock_repo,
            section_repository=AsyncMock(),
            offer_service=AsyncMock(),
            product_service=AsyncMock(),
        )
        result = await service.search_by_id(id="x")
        self.assertEqual(result, "obj")
        mock_repo.select_by_id.assert_awaited_with(id="x")

    async def test_search_all(self):
        mock_repo = AsyncMock()
        mock_repo.select_all.return_value = ["obj"]
        service = SectionItemServices(
            section_item_repository=mock_repo,
            section_repository=AsyncMock(),
            offer_service=AsyncMock(),
            product_service=AsyncMock(),
        )
        result = await service.search_all(section_id="s", is_visible=True)
        self.assertEqual(result, ["obj"])
        mock_repo.select_all.assert_awaited_with(section_id="s", is_visible=True)

    async def test_search_all_expand_offer(self):
        from app.crud.offers.schemas import CompleteOffer

        mock_repo = AsyncMock()
        so = SectionItemInDB(
            id="rel",
            organization_id="org1",
            section_id="sec",
            item_id="off",
            item_type=ItemType.OFFER,
            position=1,
            is_visible=True,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
            is_active=True,
        )
        mock_repo.select_all.return_value = [so]
        mock_offer_service = AsyncMock()
        mock_offer_service.search_by_id.return_value = CompleteOffer(
            id="off",
            organization_id="org1",
            name="Offer",
            description="d",
            unit_cost=1.0,
            unit_price=2.0,
            products=[],
            starts_at=UTCDateTime.now(),
            ends_at=UTCDateTime.now(),
            is_visible=True,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
            is_active=True,
        )
        service = SectionItemServices(
            section_item_repository=mock_repo,
            section_repository=AsyncMock(),
            offer_service=mock_offer_service,
            product_service=AsyncMock(),
        )
        result = await service.search_all(section_id="sec", expand=["items"])
        self.assertEqual(result[0].offer.id, "off")
        mock_offer_service.search_by_id.assert_awaited_with(
            id="off", expand=["items"]
        )

    async def test_search_all_expand_product(self):
        from app.crud.products.schemas import CompleteProduct, ProductKind

        mock_repo = AsyncMock()
        so = SectionItemInDB(
            id="rel",
            organization_id="org1",
            section_id="sec",
            item_id="prod",
            item_type=ItemType.PRODUCT,
            position=1,
            is_visible=True,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
            is_active=True,
        )
        mock_repo.select_all.return_value = [so]
        mock_product_service = AsyncMock()
        mock_product_service.search_by_id.return_value = CompleteProduct(
            id="prod",
            organization_id="org1",
            name="Prod",
            description="d",
            unit_cost=1.0,
            unit_price=2.0,
            kind=ProductKind.REGULAR,
            tags=[],
            additionals=[],
            file=None,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
            is_active=True,
        )
        service = SectionItemServices(
            section_item_repository=mock_repo,
            section_repository=AsyncMock(),
            offer_service=AsyncMock(),
            product_service=mock_product_service,
        )
        result = await service.search_all(section_id="sec", expand=["items"])
        self.assertEqual(result[0].product.id, "prod")
        mock_product_service.search_by_id.assert_awaited_with(
            id="prod", expand=["items"]
        )

    async def test_delete_by_id(self):
        mock_repo = AsyncMock()
        mock_repo.delete_by_id.return_value = "deleted"
        service = SectionItemServices(
            section_item_repository=mock_repo,
            section_repository=AsyncMock(),
            offer_service=AsyncMock(),
            product_service=AsyncMock(),
        )
        result = await service.delete_by_id(id="d")
        self.assertEqual(result, "deleted")
        mock_repo.delete_by_id.assert_awaited_with(id="d")
