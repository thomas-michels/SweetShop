import unittest
from unittest.mock import AsyncMock
from mongoengine import connect, disconnect
import mongomock

from app.api.dependencies.auth import decode_jwt
from app.api.dependencies.get_current_organization import check_current_organization
from app.api.composers.section_item_composite import section_item_composer
from app.application import app
from app.crud.section_items.schemas import SectionItemInDB, ItemType
from app.core.utils.utc_datetime import UTCDateTime
from tests.api.routers import client
from tests.payloads import USER_IN_DB


class TestSectionItemsQueryRouter(unittest.TestCase):
    def setUp(self):
        disconnect()
        connect(mongo_client_class=mongomock.MongoClient)
        self.mock_service = AsyncMock()
        self.test_client = client(self.mock_service, section_item_composer)

        app.dependency_overrides[decode_jwt] = lambda: USER_IN_DB
        app.dependency_overrides[check_current_organization] = lambda: "org_123"

    def tearDown(self) -> None:
        disconnect()
        app.dependency_overrides = {}

    def _section_item_in_db(self, id="rel1", item_type=ItemType.OFFER):
        return SectionItemInDB(
            id=id,
            organization_id="org_123",
            section_id="sec1",
            item_id="off1" if item_type == ItemType.OFFER else "prod1",
            item_type=item_type,
            position=1,
            is_visible=True,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
            is_active=True,
        )

    def test_get_section_items_with_results(self):
        self.mock_service.search_all.return_value = [self._section_item_in_db()]
        response = self.test_client.get(
            "/api/sections/sec1/items",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Section items found with success")
        self.assertEqual(len(response.json()["data"]), 1)
        self.mock_service.search_all.assert_awaited_with(section_id="sec1", is_visible=None, expand=[])

    def test_get_section_items_empty_returns_200_with_empty_list(self):
        self.mock_service.search_all.return_value = []
        response = self.test_client.get(
            "/api/sections/sec1/items",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"], [])
        self.assertEqual(response.json()["message"], "Section items found with success")

    def test_get_section_items_expand_items_offer(self):
        so = self._section_item_in_db()
        setattr(so, "offer", {"id": "off1"})
        self.mock_service.search_all.return_value = [so]
        response = self.test_client.get(
            "/api/sections/sec1/items?expand=items",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 200)
        self.mock_service.search_all.assert_awaited_with(
            section_id="sec1", is_visible=None, expand=["items"]
        )

    def test_get_section_items_expand_items_product(self):
        so = self._section_item_in_db(item_type=ItemType.PRODUCT)
        setattr(so, "product", {"id": "prod1"})
        self.mock_service.search_all.return_value = [so]
        response = self.test_client.get(
            "/api/sections/sec1/items?expand=items",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 200)
        self.mock_service.search_all.assert_awaited_with(
            section_id="sec1", is_visible=None, expand=["items"]
        )

