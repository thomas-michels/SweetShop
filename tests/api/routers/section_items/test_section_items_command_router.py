import unittest
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
import mongomock

from app.api.dependencies.auth import decode_jwt
from app.api.dependencies.get_current_organization import check_current_organization
from app.application import app
from app.core.utils import slugify
from app.crud.offers.models import OfferModel
from app.crud.products.models import ProductModel
from app.crud.sections.models import SectionModel
from app.crud.menus.models import MenuModel
from tests.payloads import USER_IN_DB


class TestSectionItemsCommandRouter(unittest.TestCase):
    def setUp(self):
        def override_dependency(mock):
            def _dependency():
                return mock
            return _dependency

        disconnect()
        connect(mongo_client_class=mongomock.MongoClient)
        self.test_client = TestClient(app)

        app.dependency_overrides[decode_jwt] = override_dependency(USER_IN_DB)
        app.dependency_overrides[check_current_organization] = override_dependency("org_123")
        app.user_middleware.clear()

    def tearDown(self) -> None:
        disconnect()
        app.dependency_overrides = {}

    def insert_mock_section(self, name="Section"):
        menu_name = "Menu"
        menu = MenuModel(
            name=menu_name,
            slug=slugify(menu_name),
            description="d",
            organization_id="org_123",
        )
        menu.save()
        section = SectionModel(
            name=name,
            description="d",
            organization_id="org_123",
            menu_id=str(menu.id),
            position=1,
        )
        section.save()
        return str(section.id)

    def insert_mock_offer(self, name="Offer"):
        offer = OfferModel(
            name=name,
            description="d",
            organization_id="org_123",
            unit_cost=1.0,
            unit_price=2.0,
            products=[],
            is_visible=True,
        )
        offer.save()
        return str(offer.id)

    def insert_mock_product(self, name="Product"):
        product = ProductModel(
            name=name,
            description="d",
            organization_id="org_123",
            unit_cost=1.0,
            unit_price=2.0,
            tags=[],
            kind="REGULAR",
        )
        product.save()
        return str(product.id)

    def create_section_item(self):
        section_id = self.insert_mock_section()
        offer_id = self.insert_mock_offer()
        response = self.test_client.post(
            "/api/section_items",
            json={
                "sectionId": section_id,
                "itemId": offer_id,
                "itemType": "OFFER",
                "position": 1,
                "isVisible": True,
            },
            headers={"organization-id": "org_123"},
        )
        return response.json()["data"]["id"], section_id, offer_id

    def test_post_section_item_success(self):
        section_id = self.insert_mock_section()
        offer_id = self.insert_mock_offer()
        response = self.test_client.post(
            "/api/section_items",
            json={
                "sectionId": section_id,
                "itemId": offer_id,
                "itemType": "OFFER",
                "position": 1,
                "isVisible": True,
            },
            headers={"organization-id": "org_123"},
        )
        json = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(json["message"], "Section item created with success")
        self.assertIsNotNone(json["data"]["id"])

    def test_post_section_item_with_product_success(self):
        section_id = self.insert_mock_section()
        product_id = self.insert_mock_product()
        response = self.test_client.post(
            "/api/section_items",
            json={
                "sectionId": section_id,
                "itemId": product_id,
                "itemType": "PRODUCT",
                "position": 1,
                "isVisible": True,
            },
            headers={"organization-id": "org_123"},
        )
        json = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(json["message"], "Section item created with success")
        self.assertIsNotNone(json["data"]["id"])

    def test_post_section_item_invalid_payload_returns_422(self):
        response = self.test_client.post(
            "/api/section_items",
            json={"sectionId": "sec"},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 422)

    def test_put_section_item_success(self):
        so_id, _, _ = self.create_section_item()
        response = self.test_client.put(
            f"/api/section_items/{so_id}",
            json={"position": 2},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Section item updated with success")

    def test_put_section_item_not_found(self):
        response = self.test_client.put(
            "/api/section_items/invalid",
            json={"position": 2},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "SectionItem #invalid not found")

    def test_delete_section_item_success(self):
        so_id, _, _ = self.create_section_item()
        response = self.test_client.delete(
            f"/api/section_items/{so_id}", headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Section item deleted with success")

    def test_delete_section_item_not_found(self):
        response = self.test_client.delete(
            "/api/section_items/invalid",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "SectionItem #invalid not found")

