import sys
import unittest
from types import ModuleType
from enum import Enum
from pydantic import BaseModel

from mongoengine import connect, disconnect
import mongomock

# Stub the application module to avoid importing heavy dependencies
# Stub application and API dependency modules to bypass external packages
sys.modules.setdefault("app.application", ModuleType("app.application")).app = None

deps_pkg = ModuleType("app.api.dependencies")
deps_pkg.__path__ = []  # mark as package
sys.modules.setdefault("app.api.dependencies", deps_pkg)
sys.modules.setdefault(
    "app.api.dependencies.response", ModuleType("app.api.dependencies.response")
).build_response = lambda *args, **kwargs: None
bucket = ModuleType("app.api.dependencies.bucket")
bucket.S3BucketManager = type("S3BucketManager", (), {})
sys.modules.setdefault("app.api.dependencies.bucket", bucket)

sys.modules.setdefault(
    "app.crud.fast_orders.services", ModuleType("app.crud.fast_orders.services")
).FastOrderServices = object

configs = ModuleType("app.core.configs")
configs.get_logger = lambda name: type(
    "Logger", (), {"error": lambda *args, **kwargs: None}
)
sys.modules.setdefault("app.core.configs", configs)

orders_schemas = ModuleType("app.crud.orders.schemas")

class DeliveryType(str, Enum):
    FAST_ORDER = "FAST_ORDER"


class OrderStatus(str, Enum):
    DONE = "DONE"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"


class _Delivery:
    def __init__(self, delivery_type):
        self.delivery_type = delivery_type

    def model_dump(self):
        return {"delivery_type": self.delivery_type}

orders_schemas.DeliveryType = DeliveryType
orders_schemas.OrderStatus = OrderStatus
orders_schemas.PaymentStatus = PaymentStatus
orders_schemas.Delivery = _Delivery


class OrderInDB(BaseModel):
    pass


class PaymentInOrder(BaseModel):
    pass


orders_schemas.OrderInDB = OrderInDB
orders_schemas.PaymentInOrder = PaymentInOrder
orders_schemas.RequestOrder = type("RequestOrder", (BaseModel,), {})
orders_schemas.Order = type("Order", (BaseModel,), {})
orders_schemas.UpdateOrder = type("UpdateOrder", (BaseModel,), {})
orders_schemas.CompleteOrder = type("CompleteOrder", (BaseModel,), {})

sys.modules.setdefault("app.crud.orders.schemas", orders_schemas)
sys.modules.setdefault(
    "app.crud.orders.services", ModuleType("app.crud.orders.services")
).OrderServices = object

from app.crud.fast_orders.repositories import FastOrderRepository
from app.crud.fast_orders.schemas import FastOrder, StoredProduct
from app.crud.orders.models import OrderModel
from app.crud.orders.schemas import DeliveryType, OrderStatus, PaymentStatus
from app.core.exceptions import NotFoundError
from app.core.utils.utc_datetime import UTCDateTime


class TestFastOrderRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        self.repo = FastOrderRepository(organization_id="org1")
        OrderModel.get_payments = staticmethod(
            lambda: [
                {"$set": {"id": "$_id", "payments": []}},
                {"$project": {"_id": 0}},
            ]
        )

    def tearDown(self):
        disconnect()

    async def _order_model(self, order_date: UTCDateTime = UTCDateTime.now()):
        order = OrderModel(
            organization_id="org1",
            status=OrderStatus.DONE.value,
            payment_status=PaymentStatus.PENDING.value,
            products=[
                {
                    "product_id": "p1",
                    "name": "Cake",
                    "unit_price": 2.0,
                    "unit_cost": 1.0,
                    "quantity": 1,
                }
            ],
            tags=[],
            delivery={"delivery_type": DeliveryType.FAST_ORDER.value},
            preparation_date=order_date,
            order_date=order_date,
            total_amount=10,
            additional=0,
            discount=0,
            tax=0,
            is_fast_order=True,
        )
        order.save()
        return order

    async def test_create(self):
        fast_order = FastOrder(
            products=[
                StoredProduct(
                    product_id="p1",
                    name="Cake",
                    unit_price=2.0,
                    unit_cost=1.0,
                    quantity=1,
                )
            ],
            order_date=UTCDateTime.now(),
            description=None,
            additional=0,
            discount=0,
        )
        result = await self.repo.create(fast_order=fast_order, total_amount=10)
        self.assertEqual(result.total_amount, 10)

    async def test_update(self):
        order = await self._order_model()
        updated = await self.repo.update(
            fast_order_id=str(order.id), fast_order={"description": "updated"}
        )
        self.assertEqual(updated.description, "updated")

    async def test_select_by_id_success(self):
        order = await self._order_model()
        result = await self.repo.select_by_id(id=str(order.id))
        self.assertEqual(result.id, str(order.id))

    async def test_select_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.select_by_id(id="missing")

    async def test_select_count_with_day_filter(self):
        day = UTCDateTime.now()
        await self._order_model(order_date=day)
        await self._order_model(order_date=UTCDateTime(year=2020, month=1, day=1))
        count = await self.repo.select_count(day=day)
        self.assertEqual(count, 1)

    async def test_select_all_with_pagination(self):
        await self._order_model()
        await self._order_model()
        await self._order_model()
        results = await self.repo.select_all(page=1, page_size=2)
        self.assertEqual(len(results), 2)
        results_p2 = await self.repo.select_all(page=2, page_size=2)
        self.assertEqual(len(results_p2), 1)

    async def test_delete_by_id_success(self):
        order = await self._order_model()
        deleted = await self.repo.delete_by_id(id=str(order.id))
        self.assertEqual(deleted.id, str(order.id))
        self.assertEqual(
            OrderModel.objects(is_active=True, is_fast_order=True).count(), 0
        )

    async def test_delete_by_id_not_found(self):
        result = await self.repo.delete_by_id(id="missing")
        self.assertIsNone(result)
