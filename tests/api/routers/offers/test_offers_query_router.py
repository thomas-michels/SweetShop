import unittest
from unittest.mock import AsyncMock
from mongoengine import connect, disconnect
import mongomock

from app.api.dependencies.auth import decode_jwt
from app.api.dependencies.get_current_organization import check_current_organization
from app.api.composers.offer_composite import offer_composer
from app.application import app
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.offers.schemas import OfferInDB, OfferProduct
from tests.api.routers import client
from tests.payloads import USER_IN_DB
from app.core.exceptions import NotFoundError


class TestOffersQueryRouter(unittest.TestCase):
    def setUp(self):
        disconnect()
        connect(mongo_client_class=mongomock.MongoClient)
        self.mock_service = AsyncMock()
        self.test_client = client(self.mock_service, offer_composer)

        app.dependency_overrides[decode_jwt] = lambda: USER_IN_DB
        app.dependency_overrides[check_current_organization] = lambda: "org_123"

    def tearDown(self) -> None:
        disconnect()
        app.dependency_overrides = {}

    def _offer_in_db(self, id="off1"):
        prod = OfferProduct(
            product_id="p1",
            name="P1",
            description="d",
            unit_cost=1.0,
            unit_price=2.0,
            file_id=None,
        )
        return OfferInDB(
            id=id,
            organization_id="org_123",
            name="Combo",
            description="desc",
            unit_cost=1.0,
            unit_price=2.0,
            products=[prod],
            additionals=[],
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
            is_active=True,
        )

    def test_get_offer_by_id_success(self):
        self.mock_service.search_by_id.return_value = self._offer_in_db()
        response = self.test_client.get(
            "/api/offers/off1",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Offer found with success")
        self.mock_service.search_by_id.assert_awaited_with(id="off1", expand=[])

    def test_get_offer_by_id_not_found(self):
        self.mock_service.search_by_id.side_effect = NotFoundError("Offer #off2 not found")
        response = self.test_client.get(
            "/api/offers/off2",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "Offer #off2 not found")

    def test_get_offers_with_results(self):
        self.mock_service.search_all.return_value = [self._offer_in_db()]
        response = self.test_client.get(
            "/api/sections/sec1/offers",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Offers found with success")
        self.assertEqual(len(response.json()["data"]), 1)
        self.mock_service.search_all.assert_awaited()

    def test_get_offers_empty_returns_204(self):
        self.mock_service.search_all.return_value = []
        response = self.test_client.get(
            "/api/sections/sec1/offers",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 204)
