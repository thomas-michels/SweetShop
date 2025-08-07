import unittest
from unittest.mock import AsyncMock
from mongoengine import connect, disconnect
import mongomock

from app.api.dependencies.auth import decode_jwt
from app.api.dependencies.get_current_organization import check_current_organization
from app.api.composers.section_offer_composite import section_offer_composer
from app.application import app
from app.crud.section_offers.schemas import SectionOfferInDB
from app.core.utils.utc_datetime import UTCDateTime
from tests.api.routers import client
from tests.payloads import USER_IN_DB
from app.core.exceptions import NotFoundError


class TestSectionOffersQueryRouter(unittest.TestCase):
    def setUp(self):
        disconnect()
        connect(mongo_client_class=mongomock.MongoClient)
        self.mock_service = AsyncMock()
        self.test_client = client(self.mock_service, section_offer_composer)

        app.dependency_overrides[decode_jwt] = lambda: USER_IN_DB
        app.dependency_overrides[check_current_organization] = lambda: "org_123"

    def tearDown(self) -> None:
        disconnect()
        app.dependency_overrides = {}

    def _section_offer_in_db(self, id="rel1", product=False):
        return SectionOfferInDB(
            id=id,
            organization_id="org_123",
            section_id="sec1",
            offer_id=None if product else "off1",
            product_id="prod1" if product else None,
            position=1,
            is_visible=True,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
            is_active=True,
        )

    def test_get_section_offers_with_results(self):
        self.mock_service.search_all.return_value = [self._section_offer_in_db()]
        response = self.test_client.get(
            "/api/sections/sec1/offers",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Section offers found with success")
        self.assertEqual(len(response.json()["data"]), 1)
        self.mock_service.search_all.assert_awaited_with(section_id="sec1", is_visible=None, expand=[])

    def test_get_section_offers_empty_returns_204(self):
        self.mock_service.search_all.return_value = []
        response = self.test_client.get(
            "/api/sections/sec1/offers",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 204)

    def test_get_section_offers_expand_offer(self):
        so = self._section_offer_in_db()
        setattr(so, "offer", {"id": "off1"})
        self.mock_service.search_all.return_value = [so]
        response = self.test_client.get(
            "/api/sections/sec1/offers?expand=offer",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 200)
        self.mock_service.search_all.assert_awaited_with(
            section_id="sec1", is_visible=None, expand=["offer"]
        )

    def test_get_section_offers_expand_product(self):
        so = self._section_offer_in_db(product=True)
        setattr(so, "product", {"id": "prod1"})
        self.mock_service.search_all.return_value = [so]
        response = self.test_client.get(
            "/api/sections/sec1/offers?expand=product",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 200)
        self.mock_service.search_all.assert_awaited_with(
            section_id="sec1", is_visible=None, expand=["product"]
        )

