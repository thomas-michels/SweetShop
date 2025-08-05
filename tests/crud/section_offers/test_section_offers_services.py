import unittest
from unittest.mock import AsyncMock
from mongoengine import connect, disconnect
import mongomock

from app.crud.section_offers.repositories import SectionOfferRepository
from app.crud.section_offers.schemas import SectionOffer, UpdateSectionOffer, SectionOfferInDB
from app.crud.section_offers.services import SectionOfferServices
from app.core.utils.utc_datetime import UTCDateTime


class TestSectionOfferServices(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        repo = SectionOfferRepository(organization_id="org1")
        self.section_repo = AsyncMock()
        self.offer_repo = AsyncMock()
        self.service = SectionOfferServices(
            section_offer_repository=repo,
            section_repository=self.section_repo,
            offer_repository=self.offer_repo,
        )

    def tearDown(self):
        disconnect()

    async def _section_offer(self):
        return SectionOffer(section_id="sec1", offer_id="off1", position=1, is_visible=True)

    async def test_create_section_offer(self):
        self.section_repo.select_by_id.return_value = None
        self.offer_repo.select_by_id.return_value = None
        result = await self.service.create(await self._section_offer())
        self.assertIsInstance(result, SectionOfferInDB)
        self.section_repo.select_by_id.assert_awaited_with(id="sec1")
        self.offer_repo.select_by_id.assert_awaited_with(id="off1")

    async def test_update_section_offer(self):
        self.section_repo.select_by_id.return_value = None
        self.offer_repo.select_by_id.return_value = None
        created = await self.service.create(await self._section_offer())
        updated = await self.service.update(id=created.id, updated_section_offer=UpdateSectionOffer(position=2))
        self.assertEqual(updated.position, 2)

    async def test_search_by_id_calls_repo(self):
        mock_repo = AsyncMock()
        mock_repo.select_by_id.return_value = "obj"
        service = SectionOfferServices(
            section_offer_repository=mock_repo,
            section_repository=AsyncMock(),
            offer_repository=AsyncMock(),
        )
        result = await service.search_by_id(id="x")
        self.assertEqual(result, "obj")
        mock_repo.select_by_id.assert_awaited_with(id="x")

    async def test_search_all(self):
        mock_repo = AsyncMock()
        mock_repo.select_all.return_value = ["obj"]
        service = SectionOfferServices(
            section_offer_repository=mock_repo,
            section_repository=AsyncMock(),
            offer_repository=AsyncMock(),
        )
        result = await service.search_all(section_id="s", is_visible=True)
        self.assertEqual(result, ["obj"])
        mock_repo.select_all.assert_awaited_with(section_id="s", is_visible=True)

    async def test_search_all_expand_offer(self):
        from app.crud.offers.schemas import OfferInDB

        mock_repo = AsyncMock()
        so = SectionOfferInDB(
            id="rel",
            organization_id="org1",
            section_id="sec",
            offer_id="off",
            position=1,
            is_visible=True,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
            is_active=True,
        )
        mock_repo.select_all.return_value = [so]
        mock_offer_repo = AsyncMock()
        mock_offer_repo.select_by_id.return_value = OfferInDB(
            id="off",
            organization_id="org1",
            name="Offer",
            description="d",
            unit_cost=1.0,
            unit_price=2.0,
            products=[],
            file_id=None,
            starts_at=UTCDateTime.now(),
            ends_at=UTCDateTime.now(),
            is_visible=True,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
            is_active=True,
        )
        service = SectionOfferServices(
            section_offer_repository=mock_repo,
            section_repository=AsyncMock(),
            offer_repository=mock_offer_repo,
        )
        result = await service.search_all(section_id="sec", expand=["offer"])
        self.assertEqual(result[0].offer.id, "off")
        mock_offer_repo.select_by_id.assert_awaited_with(id="off", raise_404=False)

    async def test_delete_by_id(self):
        mock_repo = AsyncMock()
        mock_repo.delete_by_id.return_value = "deleted"
        service = SectionOfferServices(
            section_offer_repository=mock_repo,
            section_repository=AsyncMock(),
            offer_repository=AsyncMock(),
        )
        result = await service.delete_by_id(id="d")
        self.assertEqual(result, "deleted")
        mock_repo.delete_by_id.assert_awaited_with(id="d")
