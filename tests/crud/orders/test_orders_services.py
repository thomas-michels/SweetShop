import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.api.exceptions.authentication_exceptions import UnauthorizedException
from app.crud.orders.schemas import (
    Delivery,
    DeliveryType,
    OrderInDB,
    OrderStatus,
    RequestOrder,
    RequestedProduct,
    StoredProduct,
)
from app.crud.orders.services import OrderServices
from app.crud.shared_schemas.payment import PaymentStatus
from app.core.utils.utc_datetime import UTCDateTime


class TestOrderServices(unittest.IsolatedAsyncioTestCase):
    def _order_in_db(self):
        return OrderInDB(
            id="ord1",
            organization_id="org1",
            customer_id="c1",
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            products=[
                StoredProduct(
                    product_id="p1",
                    name="Cake",
                    unit_price=2.0,
                    unit_cost=1.0,
                    quantity=1,
                )
            ],
            tags=["t1"],
            delivery=Delivery(delivery_type=DeliveryType.WITHDRAWAL),
            preparation_date=UTCDateTime.now(),
            order_date=UTCDateTime.now(),
            total_amount=10,
            description=None,
            additional=0,
            discount=0,
            payments=[],
            tax=0,
            reason_id=None,
            is_active=True,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )

    @patch("app.crud.orders.services.get_plan_feature", new_callable=AsyncMock)
    async def test_create_order_respects_plan_limit(self, mock_plan):
        repo = AsyncMock()
        repo.select_count_by_date.return_value = 1
        service = OrderServices(
            order_repository=repo,
            product_repository=AsyncMock(),
            tag_repository=AsyncMock(),
            customer_repository=AsyncMock(),
            organization_repository=AsyncMock(),
        )
        mock_plan.return_value = SimpleNamespace(value="1")
        req = RequestOrder(
            products=[RequestedProduct(product_id="p1", quantity=1)],
            tags=[],
            delivery=Delivery(delivery_type=DeliveryType.WITHDRAWAL),
            preparation_date=UTCDateTime.now(),
            order_date=UTCDateTime.now(),
        )
        with self.assertRaises(UnauthorizedException):
            await service.create(req)

    @patch("app.crud.orders.services.get_plan_feature", new_callable=AsyncMock)
    async def test_create_order_success(self, mock_plan):
        repo = AsyncMock()
        repo.select_count_by_date.return_value = 0
        repo.create.return_value = self._order_in_db()
        product_repo = AsyncMock()
        product_repo.select_by_id.return_value = SimpleNamespace(
            name="Cake", unit_cost=1.0, unit_price=2.0
        )
        tag_repo = AsyncMock()
        customer_repo = AsyncMock()
        organization_repo = AsyncMock()
        organization_repo.select_by_id.return_value = SimpleNamespace(tax=0)
        service = OrderServices(
            order_repository=repo,
            product_repository=product_repo,
            tag_repository=tag_repo,
            customer_repository=customer_repo,
            organization_repository=organization_repo,
        )
        service._OrderServices__order_calculator.calculate = AsyncMock(return_value=10)
        mock_plan.return_value = SimpleNamespace(value="-")
        req = RequestOrder(
            products=[RequestedProduct(product_id="p1", quantity=1)],
            tags=[],
            delivery=Delivery(delivery_type=DeliveryType.WITHDRAWAL),
            preparation_date=UTCDateTime.now(),
            order_date=UTCDateTime.now(),
        )
        result = await service.create(req)
        repo.create.assert_awaited()
        self.assertEqual(result.total_amount, 10)

    async def test_search_by_id_expand(self):
        repo = AsyncMock()
        repo.select_by_id.return_value = self._order_in_db()
        customer_repo = AsyncMock()
        customer_repo.select_by_id.return_value = "cust"
        tag_repo = AsyncMock()
        tag_repo.select_by_id.return_value = "tag"
        service = OrderServices(
            order_repository=repo,
            product_repository=AsyncMock(),
            tag_repository=tag_repo,
            customer_repository=customer_repo,
            organization_repository=AsyncMock(),
        )
        result = await service.search_by_id(
            id="ord1", expand=["customers", "tags"]
        )
        customer_repo.select_by_id.assert_awaited()
        tag_repo.select_by_id.assert_awaited()
        self.assertEqual(result.customer, "cust")
        self.assertEqual(result.tags, ["tag"])

    async def test_search_count(self):
        repo = AsyncMock()
        repo.select_count.return_value = 3
        service = OrderServices(
            order_repository=repo,
            product_repository=AsyncMock(),
            tag_repository=AsyncMock(),
            customer_repository=AsyncMock(),
            organization_repository=AsyncMock(),
        )
        count = await service.search_count(
            status=None,
            payment_status=[],
            delivery_type=None,
            customer_id=None,
            start_date=None,
            end_date=None,
            tags=[],
            min_total_amount=None,
            max_total_amount=None,
        )
        self.assertEqual(count, 3)
        repo.select_count.assert_awaited()

    async def test_delete_by_id(self):
        repo = AsyncMock()
        repo.delete_by_id.return_value = self._order_in_db()
        service = OrderServices(
            order_repository=repo,
            product_repository=AsyncMock(),
            tag_repository=AsyncMock(),
            customer_repository=AsyncMock(),
            organization_repository=AsyncMock(),
        )
        result = await service.delete_by_id(id="ord1")
        repo.delete_by_id.assert_awaited_with(id="ord1")
        self.assertEqual(result.id, "ord1")
