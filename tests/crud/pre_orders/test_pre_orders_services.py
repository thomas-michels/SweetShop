import unittest
from unittest.mock import AsyncMock
from mongoengine import connect, disconnect
import mongomock

from app.crud.pre_orders.repositories import PreOrderRepository
from app.crud.pre_orders.services import PreOrderServices
from app.crud.pre_orders.schemas import (
    PreOrderStatus,
    SelectedAdditional,
    SelectedItem,
    SelectedOffer,
    SelectedProduct,
)
from enum import Enum
from pydantic import BaseModel
from app.core.utils.utc_datetime import UTCDateTime
from app.api.exceptions.authentication_exceptions import BadRequestException


class OptionKind(str, Enum):
    CHECKBOX = "CHECKBOX"


class AdditionalItemInDB(BaseModel):
    id: str
    organization_id: str
    additional_id: str
    position: int
    product_id: str
    label: str
    unit_price: float
    unit_cost: float
    consumption_factor: float
    created_at: UTCDateTime
    updated_at: UTCDateTime


class ProductAdditionalInDB(BaseModel):
    id: str
    organization_id: str
    product_id: str
    name: str
    selection_type: OptionKind
    min_quantity: int
    max_quantity: int
    position: int
    items: list
    created_at: UTCDateTime
    updated_at: UTCDateTime


class DummyOrg:
    international_code = "55"
    ddd = "047"
    phone_number = "123456789"


class TestPreOrderServices(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        repo = PreOrderRepository(organization_id="org1")
        self.customer_repo = AsyncMock()
        self.offer_repo = AsyncMock()
        self.organization_repo = AsyncMock()
        self.message_services = AsyncMock()
        self.additional_repo = AsyncMock()
        self.product_additional_repo = AsyncMock()
        self.service = PreOrderServices(
            pre_order_repository=repo,
            customer_repository=self.customer_repo,
            offer_repository=self.offer_repo,
            organization_repository=self.organization_repo,
            message_services=self.message_services,
            additional_item_repository=self.additional_repo,
            product_additional_repository=self.product_additional_repo,
        )

    def tearDown(self):
        disconnect()

    def _pre_order_model(self, code="001", status=PreOrderStatus.PENDING):
        return {
            "organization_id": "org1",
            "code": code,
            "menu_id": "men1",
            "payment_method": "CASH",
            "customer": {"name": "Ted", "ddd": "047", "phone_number": "9988"},
            "delivery": {"delivery_type": "WITHDRAWAL"},
            "offers": [{"offer_id": "off1", "quantity": 1}],
            "products": [],
            "status": status.value,
            "tax": 0,
            "total_amount": 10,
        }

    async def test_update_status(self):
        from app.crud.pre_orders.models import PreOrderModel
        pre = PreOrderModel(**self._pre_order_model())
        pre.save()
        self.customer_repo.select_by_phone.return_value = None
        self.organization_repo.select_by_id.return_value = DummyOrg()
        updated = await self.service.update_status(pre.id, PreOrderStatus.ACCEPTED)
        self.assertEqual(updated.status, PreOrderStatus.ACCEPTED)
        self.message_services.create.assert_awaited()

    async def test_search_all(self):
        from app.crud.pre_orders.models import PreOrderModel
        PreOrderModel(**self._pre_order_model(code="A")).save()
        PreOrderModel(**self._pre_order_model(code="B")).save()
        self.customer_repo.select_by_phone.return_value = None
        result = await self.service.search_all()
        self.assertEqual(len(result), 2)

    async def test_search_count(self):
        mock_repo = AsyncMock()
        mock_repo.select_count.return_value = 2
        service = PreOrderServices(
            pre_order_repository=mock_repo,
            customer_repository=AsyncMock(),
            offer_repository=AsyncMock(),
            organization_repository=AsyncMock(),
            message_services=AsyncMock(),
            additional_item_repository=AsyncMock(),
            product_additional_repository=AsyncMock(),
        )
        count = await service.search_count()
        self.assertEqual(count, 2)
        mock_repo.select_count.assert_awaited()

    async def test_delete_by_id(self):
        from app.crud.pre_orders.models import PreOrderModel
        pre = PreOrderModel(**self._pre_order_model())
        pre.save()
        deleted = await self.service.delete_by_id(pre.id)
        self.assertEqual(deleted.id, pre.id)

    async def test_validate_offers_with_additionals(self):
        self.additional_repo.select_by_id.return_value = AdditionalItemInDB(
            id="a1",
            organization_id="org1",
            additional_id="add1",
            position=1,
            product_id="p1",
            label="Extra",
            unit_price=1.0,
            unit_cost=0.5,
            consumption_factor=1.0,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )
        self.product_additional_repo.select_by_product_id.return_value = [
            ProductAdditionalInDB(
                id="add1",
                organization_id="org1",
                product_id="p1",
                name="Group",
                selection_type=OptionKind.CHECKBOX,
                min_quantity=0,
                max_quantity=1,
                position=1,
                items=[],
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
            )
        ]

        offer = SelectedOffer(
            offer_id="off1",
            quantity=1,
            items=[
                SelectedItem(
                    item_id="p1",
                    section_id="s1",
                    name="Prod1",
                    unit_price=2.0,
                    unit_cost=1.0,
                    quantity=1,
                    additionals=[
                        SelectedAdditional(additional_id="add1", item_id="a1", quantity=1)
                    ],
                )
            ],
        )

        offers = await self.service._PreOrderServices__validate_offers([offer])

        self.assertEqual(offers[0].items[0].unit_price, 3.0)
        self.assertEqual(offers[0].items[0].unit_cost, 1.5)
        self.additional_repo.select_by_id.assert_awaited_with(id="a1")
        self.product_additional_repo.select_by_product_id.assert_awaited_with(product_id="p1")

    async def test_validate_offers_max_quantity(self):
        self.additional_repo.select_by_id.return_value = AdditionalItemInDB(
            id="a1",
            organization_id="org1",
            additional_id="add1",
            position=1,
            product_id="p1",
            label="Extra",
            unit_price=1.0,
            unit_cost=0.5,
            consumption_factor=1.0,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )
        self.product_additional_repo.select_by_product_id.return_value = [
            ProductAdditionalInDB(
                id="add1",
                organization_id="org1",
                product_id="p1",
                name="Group",
                selection_type=OptionKind.CHECKBOX,
                min_quantity=0,
                max_quantity=1,
                position=1,
                items=[],
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
            )
        ]

        offer = SelectedOffer(
            offer_id="off1",
            quantity=1,
            items=[
                SelectedItem(
                    item_id="p1",
                    section_id="s1",
                    name="Prod1",
                    unit_price=2.0,
                    unit_cost=1.0,
                    quantity=1,
                    additionals=[
                        SelectedAdditional(additional_id="add1", item_id="a1", quantity=2)
                    ],
                )
            ],
        )

        with self.assertRaises(BadRequestException):
            await self.service._PreOrderServices__validate_offers([offer])

    async def test_validate_products_with_additionals(self):
        self.additional_repo.select_by_id.return_value = AdditionalItemInDB(
            id="a1",
            organization_id="org1",
            additional_id="add1",
            position=1,
            product_id="p1",
            label="Extra",
            unit_price=1.0,
            unit_cost=0.5,
            consumption_factor=1.0,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )
        self.product_additional_repo.select_by_product_id.return_value = [
            ProductAdditionalInDB(
                id="add1",
                organization_id="org1",
                product_id="p1",
                name="Group",
                selection_type=OptionKind.CHECKBOX,
                min_quantity=0,
                max_quantity=1,
                position=1,
                items=[],
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
            )
        ]

        product = SelectedProduct(
            product_id="p1",
            section_id="s1",
            name="Prod1",
            unit_price=2.0,
            unit_cost=1.0,
            quantity=1,
            additionals=[
                SelectedAdditional(additional_id="add1", item_id="a1", quantity=1)
            ],
        )

        products = await self.service._PreOrderServices__validate_products([product])

        self.assertEqual(products[0].unit_price, 3.0)
        self.assertEqual(products[0].unit_cost, 1.5)
        self.additional_repo.select_by_id.assert_awaited_with(id="a1")
        self.product_additional_repo.select_by_product_id.assert_awaited_with(product_id="p1")

    async def test_validate_products_max_quantity(self):
        self.additional_repo.select_by_id.return_value = AdditionalItemInDB(
            id="a1",
            organization_id="org1",
            additional_id="add1",
            position=1,
            product_id="p1",
            label="Extra",
            unit_price=1.0,
            unit_cost=0.5,
            consumption_factor=1.0,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )
        self.product_additional_repo.select_by_product_id.return_value = [
            ProductAdditionalInDB(
                id="add1",
                organization_id="org1",
                product_id="p1",
                name="Group",
                selection_type=OptionKind.CHECKBOX,
                min_quantity=0,
                max_quantity=1,
                position=1,
                items=[],
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
            )
        ]

        product = SelectedProduct(
            product_id="p1",
            section_id="s1",
            name="Prod1",
            unit_price=2.0,
            unit_cost=1.0,
            quantity=1,
            additionals=[
                SelectedAdditional(additional_id="add1", item_id="a1", quantity=2)
            ],
        )

        with self.assertRaises(BadRequestException):
            await self.service._PreOrderServices__validate_products([product])
