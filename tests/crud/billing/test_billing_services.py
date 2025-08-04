import unittest
from types import SimpleNamespace
from typing import List
from unittest.mock import AsyncMock, patch

from app.crud.billing.services import BillingServices
from app.crud.orders.schemas import (
    Delivery,
    DeliveryType,
    OrderInDB,
    OrderStatus,
    PaymentInOrder,
)
from app.crud.expenses.schemas import ExpenseInDB
from app.crud.shared_schemas.payment import Payment, PaymentMethod, PaymentStatus
from app.core.utils.utc_datetime import UTCDateTime


class TestBillingServices(unittest.IsolatedAsyncioTestCase):
    async def _order(
        self,
        order_id: str,
        total: float,
        payments: List[PaymentInOrder],
    ) -> OrderInDB:
        now = UTCDateTime.now()
        return OrderInDB(
            id=order_id,
            organization_id="org1",
            customer_id=None,
            status=OrderStatus.DONE,
            payment_status=PaymentStatus.PAID,
            products=[],
            tags=[],
            delivery=Delivery(delivery_type=DeliveryType.WITHDRAWAL),
            preparation_date=now,
            order_date=now,
            description=None,
            additional=0,
            discount=0,
            total_amount=total,
            tax=0,
            payments=payments,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    async def _expense(self, expense_id: str, total: float) -> ExpenseInDB:
        now = UTCDateTime.now()
        return ExpenseInDB(
            id=expense_id,
            name="Expense",
            expense_date=now,
            payment_details=[
                Payment(method=PaymentMethod.CASH, payment_date=now, amount=total)
            ],
            tags=[],
            organization_id="org1",
            total_paid=total,
            created_at=now,
            updated_at=now,
        )

    @patch("app.crud.billing.services.RedisManager")
    @patch("app.crud.billing.services.get_plan_feature", new_callable=AsyncMock)
    async def test_get_billing_for_dashboard_calculates_totals(
        self, mock_plan, mock_redis
    ):
        mock_plan.return_value = SimpleNamespace(value="true")
        mock_redis.return_value.get_value.return_value = None

        mock_order_services = AsyncMock()
        mock_expense_services = AsyncMock()
        mock_fast_order_services = AsyncMock()

        now = UTCDateTime.now()
        order1_payments = [
            PaymentInOrder(
                id="p1",
                order_id="o1",
                method=PaymentMethod.CASH,
                payment_date=now,
                amount=10,
                created_at=now,
                updated_at=now,
            ),
            PaymentInOrder(
                id="p2",
                order_id="o1",
                method=PaymentMethod.PIX,
                payment_date=now,
                amount=10,
                created_at=now,
                updated_at=now,
            ),
            PaymentInOrder(
                id="p3",
                order_id="o1",
                method=PaymentMethod.CREDIT_CARD,
                payment_date=now,
                amount=5,
                created_at=now,
                updated_at=now,
            ),
        ]
        order2_payments = [
            PaymentInOrder(
                id="p4",
                order_id="o2",
                method=PaymentMethod.DEBIT_CARD,
                payment_date=now,
                amount=20,
                created_at=now,
                updated_at=now,
            )
        ]

        order1 = await self._order("o1", 30, order1_payments)
        order2 = await self._order("o2", 20, order2_payments)
        mock_order_services.search_all_without_filters.return_value = [order1, order2]

        expense1 = await self._expense("e1", 5)
        expense2 = await self._expense("e2", 7.5)
        mock_expense_services.search_all.return_value = [expense1, expense2]

        service = BillingServices(
            product_repository=AsyncMock(),
            order_services=mock_order_services,
            fast_order_services=mock_fast_order_services,
            expenses_services=mock_expense_services,
        )

        billing = await service.get_billing_for_dashboard(month=now.month, year=now.year)

        self.assertEqual(billing.total_amount, 50)
        self.assertEqual(billing.payment_received, 45)
        self.assertEqual(billing.cash_received, 10)
        self.assertEqual(billing.pix_received, 10)
        self.assertEqual(billing.credit_card_received, 5)
        self.assertEqual(billing.debit_card_received, 20)
        self.assertEqual(billing.zelle_received, 0)
        self.assertEqual(billing.pending_payments, 5)
        self.assertEqual(billing.total_expanses, 12.5)
