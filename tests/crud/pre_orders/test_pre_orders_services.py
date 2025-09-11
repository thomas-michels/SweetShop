import unittest
from unittest.mock import AsyncMock
from mongoengine import connect, disconnect
import mongomock

from app.crud.pre_orders.repositories import PreOrderRepository
from app.crud.pre_orders.services import PreOrderServices
from app.crud.pre_orders.schemas import PreOrderStatus
from types import SimpleNamespace
from app.core.utils.utc_datetime import UTCDateTime


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
            "user_id": "usr1",
            "code": code,
            "menu_id": "men1",
            "payment_method": "CASH",
            "customer": {"name": "Ted", "ddd": "047", "phone_number": "9988"},
            "delivery": {"delivery_type": "WITHDRAWAL"},
            "items": [],
            "status": status.value,
            "tax": 0,
            "total_amount": 10,
            "total_cost": 5,
        }

    async def test_update_status(self):
        from app.crud.pre_orders.models import PreOrderModel
        model = self._pre_order_model()
        model["items"] = [
            {
                "product_id": "p1",
                "section_id": "s1",
                "name": "Prod1",
                "file_id": None,
                "unit_price": 1.0,
                "unit_cost": 0.5,
                "quantity": 1,
                "additionals": [],
            }
        ]
        pre = PreOrderModel(**model)
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

    async def test_reject_pre_order(self):
        from app.crud.pre_orders.models import PreOrderModel

        model = self._pre_order_model()
        model["items"] = [
            {
                "product_id": "p1",
                "section_id": "s1",
                "name": "Prod1",
                "file_id": None,
                "unit_price": 1.0,
                "unit_cost": 0.5,
                "quantity": 1,
                "additionals": [],
            }
        ]
        pre = PreOrderModel(**model)
        pre.save()

        self.customer_repo.select_by_phone.return_value = None
        self.organization_repo.select_by_id.return_value = DummyOrg()

        rejected = await self.service.reject_pre_order(pre.id)

        self.assertEqual(rejected.status, PreOrderStatus.REJECTED)
        self.message_services.create.assert_awaited()

    async def test_accept_pre_order_existing_customer_adds_address(self):
        from app.crud.pre_orders.models import PreOrderModel

        model = self._pre_order_model()
        model["delivery"] = {
            "delivery_type": "DELIVERY",
            "delivery_value": 0,
            "delivery_at": str(UTCDateTime.now()),
            "address": {
                "zip_code": "89066-000",
                "city": "Blumenau",
                "neighborhood": "Bairro dos testes",
                "line_1": "Rua de teste",
                "line_2": "Casa",
                "number": "123A",
            },
        }
        model["items"] = [
            {
                "product_id": "p1",
                "section_id": "s1",
                "name": "Prod1",
                "file_id": None,
                "unit_price": 1.0,
                "unit_cost": 0.5,
                "quantity": 1,
                "additionals": [],
            }
        ]
        pre = PreOrderModel(**model)
        pre.save()

        existing_customer = SimpleNamespace(id="cus1", addresses=[])

        self.customer_repo.select_by_phone.return_value = existing_customer
        self.customer_repo.update.return_value = existing_customer
        self.organization_repo.select_by_id.return_value = DummyOrg()

        mock_order_services = AsyncMock()
        mock_order_services.create.return_value = SimpleNamespace(id="ord1")

        order = await self.service.accept_pre_order(pre.id, mock_order_services)

        self.assertEqual(order.id, "ord1")
        pre_in_db = await self.service.search_by_id(pre.id)
        self.assertEqual(pre_in_db.order_id, "ord1")
        self.customer_repo.update.assert_awaited()
        updated_customer = self.customer_repo.update.call_args.kwargs["customer"]
        self.assertEqual(updated_customer.addresses[0].zip_code, "89066-000")
        mock_order_services.create.assert_awaited()
        self.message_services.create.assert_awaited()

    async def test_accept_pre_order_creates_customer_with_address(self):
        from app.crud.pre_orders.models import PreOrderModel

        model = self._pre_order_model()
        model["customer"]["phone_number"] = "99887766"
        model["delivery"] = {
            "delivery_type": "DELIVERY",
            "delivery_value": 0,
            "delivery_at": str(UTCDateTime.now()),
            "address": {
                "zip_code": "89066-000",
                "city": "Blumenau",
                "neighborhood": "Bairro dos testes",
                "line_1": "Rua de teste",
                "line_2": "Casa",
                "number": "123A",
            },
        }
        model["items"] = [
            {
                "product_id": "p1",
                "section_id": "s1",
                "name": "Prod1",
                "file_id": None,
                "unit_price": 1.0,
                "unit_cost": 0.5,
                "quantity": 1,
                "additionals": [],
            }
        ]
        pre = PreOrderModel(**model)
        pre.save()

        created_customer = SimpleNamespace(id="cus1", addresses=[])

        self.customer_repo.select_by_phone.return_value = None
        self.customer_repo.create.return_value = created_customer
        self.organization_repo.select_by_id.return_value = DummyOrg()

        mock_order_services = AsyncMock()
        mock_order_services.create.return_value = SimpleNamespace(id="ord1")

        order = await self.service.accept_pre_order(pre.id, mock_order_services)

        self.assertEqual(order.id, "ord1")
        self.customer_repo.create.assert_awaited()
        created_customer_arg = self.customer_repo.create.call_args.kwargs["customer"]
        self.assertEqual(created_customer_arg.addresses[0].zip_code, "89066-000")
        mock_order_services.create.assert_awaited()
        self.message_services.create.assert_awaited()

    async def test_accept_pre_order_with_offer_discount_and_additionals(self):
        from app.crud.pre_orders.models import PreOrderModel

        model = self._pre_order_model()
        model["items"] = [
            {
                "kind": "OFFER",
                "offer_id": "off1",
                "name": "Combo Deluxe",
                "unit_price": 35.0,
                "unit_cost": 17.5,
                "quantity": 2,
                "items": [
                    {
                        "item_id": "p1",
                        "name": "Prod1",
                        "file_id": None,
                        "unit_price": 10.0,
                        "unit_cost": 5.0,
                        "quantity": 2,
                        "additionals": [
                            {
                                "additional_id": "pa1",
                                "item_id": "a1",
                                "name": "Add1",
                                "unit_price": 2.0,
                                "unit_cost": 1.0,
                                "quantity": 1,
                            },
                            {
                                "additional_id": "pa2",
                                "item_id": "a2",
                                "name": "Add2",
                                "unit_price": 1.0,
                                "unit_cost": 0.5,
                                "quantity": 2,
                            },
                        ],
                    },
                    {
                        "item_id": "p2",
                        "name": "Prod2",
                        "file_id": None,
                        "unit_price": 8.0,
                        "unit_cost": 4.0,
                        "quantity": 1,
                        "additionals": [
                            {
                                "additional_id": "pa3",
                                "item_id": "a3",
                                "name": "Add3",
                                "unit_price": 0.5,
                                "unit_cost": 0.2,
                                "quantity": 4,
                            }
                        ],
                    },
                ],
                "additionals": [],
            }
        ]
        pre = PreOrderModel(**model)
        pre.save()

        existing_customer = SimpleNamespace(id="cus1", addresses=[])

        self.customer_repo.select_by_phone.return_value = existing_customer
        self.organization_repo.select_by_id.return_value = DummyOrg()

        mock_order_services = AsyncMock()
        mock_order_services.create.return_value = SimpleNamespace(id="ord1")

        order = await self.service.accept_pre_order(pre.id, mock_order_services)

        self.assertEqual(order.id, "ord1")
        mock_order_services.create.assert_awaited()
        created_order = mock_order_services.create.call_args.kwargs["order"]

        # With the corrected discount calculation, additionals are no longer
        # subtracted from the final value. Therefore, the expected discount is
        # zero and the order total must match the sum of item prices plus the
        # additional items.
        self.assertEqual(created_order.discount, 0.0)

        products = created_order.products
        self.assertEqual(len(products), 2)
        self.assertEqual(products[0].product_id, "p1")
        self.assertEqual(products[0].quantity, 4)
        self.assertEqual(len(products[0].additionals), 2)
        self.assertEqual(products[0].additionals[0].item_id, "a1")
        self.assertEqual(products[0].additionals[0].quantity, 1)
        self.assertEqual(products[0].additionals[1].item_id, "a2")
        self.assertEqual(products[0].additionals[1].quantity, 2)
        self.assertEqual(products[1].product_id, "p2")
        self.assertEqual(products[1].quantity, 2)
        self.assertEqual(len(products[1].additionals), 1)
        self.assertEqual(products[1].additionals[0].item_id, "a3")
        self.assertEqual(products[1].additionals[0].quantity, 4)

        # compute total amount manually to ensure it matches the expected
        # pre-order total (base items + additionals)
        product_prices = {"p1": 10.0, "p2": 8.0}
        additional_prices = {"a1": 2.0, "a2": 1.0, "a3": 0.5}

        order_total = 0.0
        for prod in products:
            order_total += product_prices[prod.product_id] * prod.quantity
            for add in prod.additionals:
                order_total += (
                    additional_prices[add.item_id] * add.quantity * prod.quantity
                )

        order_total -= created_order.discount

        # items base total = 56, additionals = 20 -> total 76
        self.assertAlmostEqual(order_total, 76.0)

    async def test_accept_pre_order_total_amount_matches_order(self):
        """Ensure order total matches pre-order total amount after acceptance."""
        from app.crud.pre_orders.models import PreOrderModel

        model = self._pre_order_model()
        model["items"] = [
            {
                "product_id": "p1",
                "section_id": "s1",
                "name": "Prod1",
                "file_id": None,
                "unit_price": 5.0,
                "unit_cost": 2.5,
                "quantity": 2,
                "additionals": [
                    {
                        "additional_id": "pa1",
                        "item_id": "a1",
                        "name": "Add1",
                        "unit_price": 1.0,
                        "unit_cost": 0.5,
                        "quantity": 1,
                    }
                ],
            }
        ]

        # total = (5 * 2) + (1 * 1 * 2) = 12
        model["total_amount"] = 12.0
        pre = PreOrderModel(**model)
        pre.save()

        existing_customer = SimpleNamespace(id="cus1", addresses=[])

        self.customer_repo.select_by_phone.return_value = existing_customer
        self.organization_repo.select_by_id.return_value = DummyOrg()

        mock_order_services = AsyncMock()
        mock_order_services.create.return_value = SimpleNamespace(id="ord1")

        await self.service.accept_pre_order(pre.id, mock_order_services)

        created_order = mock_order_services.create.call_args.kwargs["order"]

        product_prices = {"p1": 5.0}
        additional_prices = {"a1": 1.0}

        order_total = 0.0
        for prod in created_order.products:
            order_total += product_prices[prod.product_id] * prod.quantity
            for add in prod.additionals:
                order_total += (
                    additional_prices[add.item_id] * add.quantity * prod.quantity
                )

        order_total -= created_order.discount

        pre_after = await self.service.search_by_id(pre.id)

        self.assertAlmostEqual(order_total, pre_after.total_amount)
