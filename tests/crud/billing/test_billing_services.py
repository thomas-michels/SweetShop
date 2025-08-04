import unittest
from types import SimpleNamespace
from typing import List
from unittest.mock import AsyncMock, patch

from app.crud.billing.services import BillingServices
from app.crud.billing.schemas import (
    Billing,
    DailySale,
    ExpanseCategory,
    ProductProfit,
    SellingProduct,
)
from app.crud.orders.schemas import (
    Delivery,
    DeliveryType,
    OrderInDB,
    OrderStatus,
    PaymentInOrder,
    StoredProduct,
)
from app.crud.expenses.schemas import CompleteExpense
from app.crud.products.schemas import ProductInDB, ProductKind
from app.crud.tags.schemas import TagInDB
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

    async def _expense(
        self, expense_id: str, total: float, tags: List[TagInDB] | None = None
    ) -> CompleteExpense:
        now = UTCDateTime.now()
        return CompleteExpense.model_construct(
            id=expense_id,
            name="Expense",
            expense_date=now,
            payment_details=[
                Payment(method=PaymentMethod.CASH, payment_date=now, amount=total)
            ],
            tags=tags or [],
            organization_id="org1",
            total_paid=total,
            created_at=now,
            updated_at=now,
        )

    async def _order_with_products(
        self,
        order_id: str,
        products: List[StoredProduct],
        order_date: UTCDateTime,
        additional: float = 0,
        discount: float = 0,
    ) -> OrderInDB:
        total_amount = sum(p.unit_price * p.quantity for p in products)
        total_amount += additional - discount
        return OrderInDB(
            id=order_id,
            organization_id="org1",
            customer_id=None,
            status=OrderStatus.DONE,
            payment_status=PaymentStatus.PAID,
            products=products,
            tags=[],
            delivery=Delivery(delivery_type=DeliveryType.WITHDRAWAL),
            preparation_date=order_date,
            order_date=order_date,
            description=None,
            additional=additional,
            discount=discount,
            total_amount=total_amount,
            tax=0,
            payments=[],
            is_active=True,
            created_at=order_date,
            updated_at=order_date,
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

    @patch("app.crud.billing.services.RedisManager")
    @patch("app.crud.billing.services.get_plan_feature", new_callable=AsyncMock)
    async def test_get_monthly_billings_returns_list(self, mock_plan, mock_redis):
        mock_plan.return_value = SimpleNamespace(value="true")
        mock_redis.return_value.get_value.return_value = None

        service = BillingServices(
            product_repository=AsyncMock(),
            order_services=AsyncMock(),
            fast_order_services=AsyncMock(),
            expenses_services=AsyncMock(),
        )

        service._BillingServices__generate_monthly_billing = AsyncMock(
            side_effect=[
                Billing(month=5, year=2024, total_amount=10),
                Billing(month=4, year=2024, total_amount=20),
            ]
        )

        billings = await service.get_monthly_billings(last_months=2)

        self.assertEqual(len(billings), 2)
        self.assertEqual(billings[0].month, 5)
        self.assertEqual(billings[1].month, 4)

    @patch("app.crud.billing.services.RedisManager")
    @patch("app.crud.billing.services.get_plan_feature", new_callable=AsyncMock)
    async def test_get_best_selling_products_returns_top(self, mock_plan, mock_redis):
        mock_plan.return_value = SimpleNamespace(value="true")
        mock_redis.return_value.get_value.return_value = None

        mock_order_services = AsyncMock()
        mock_order_services.search_all_without_filters.return_value = [
            await self._order_with_products(
                "o1",
                [
                    StoredProduct(
                        product_id="p1",
                        name="Prod1",
                        unit_price=10,
                        unit_cost=5,
                        quantity=2,
                    ),
                    StoredProduct(
                        product_id="p2",
                        name="Prod2",
                        unit_price=8,
                        unit_cost=4,
                        quantity=1,
                    ),
                ],
                UTCDateTime(2024, 5, 1),
            ),
            await self._order_with_products(
                "o2",
                [
                    StoredProduct(
                        product_id="p1",
                        name="Prod1",
                        unit_price=10,
                        unit_cost=5,
                        quantity=1,
                    )
                ],
                UTCDateTime(2024, 5, 2),
            ),
        ]

        service = BillingServices(
            product_repository=AsyncMock(),
            order_services=mock_order_services,
            fast_order_services=AsyncMock(),
            expenses_services=AsyncMock(),
        )

        selling_products = await service.get_best_selling_products(month=5, year=2024)

        self.assertEqual(len(selling_products), 2)
        self.assertEqual(selling_products[0].product_id, "p1")
        self.assertEqual(selling_products[0].quantity, 2)
        self.assertEqual(selling_products[1].product_id, "p2")
        self.assertEqual(selling_products[1].quantity, 1)

    @patch("app.crud.billing.services.RedisManager")
    @patch("app.crud.billing.services.get_plan_feature", new_callable=AsyncMock)
    async def test_get_expanses_categories_sums_by_tag(self, mock_plan, mock_redis):
        mock_plan.return_value = SimpleNamespace(value="true")
        mock_redis.return_value.get_value.return_value = None

        tag1 = TagInDB(id="t1", name="Food", organization_id="org1")
        tag2 = TagInDB(id="t2", name="Rent", organization_id="org1")

        mock_expense_services = AsyncMock()
        mock_expense_services.search_all.return_value = [
            await self._expense("e1", 10, tags=[tag1]),
            await self._expense("e2", 20, tags=[tag1]),
            await self._expense("e3", 5, tags=[tag2]),
        ]

        service = BillingServices(
            product_repository=AsyncMock(),
            order_services=AsyncMock(),
            fast_order_services=AsyncMock(),
            expenses_services=mock_expense_services,
        )

        categories = await service.get_expanses_categories(month=5, year=2024)

        self.assertEqual(len(categories), 2)
        self.assertEqual(categories[0].tag_id, "t1")
        self.assertEqual(categories[0].total_paid, 30)
        self.assertEqual(categories[1].tag_id, "t2")
        self.assertEqual(categories[1].total_paid, 5)

    @patch("app.crud.billing.services.RedisManager")
    @patch("app.crud.billing.services.get_plan_feature", new_callable=AsyncMock)
    async def test_get_products_profit_calculates_profit(self, mock_plan, mock_redis):
        mock_plan.return_value = SimpleNamespace(value="true")
        mock_redis.return_value.get_value.return_value = None

        product_repository = AsyncMock()
        now = UTCDateTime.now()
        product_repository.select_by_id.side_effect = [
            ProductInDB(
                id="p1",
                name="Prod1",
                description="desc",
                unit_price=10,
                unit_cost=6,
                kind=ProductKind.REGULAR,
                tags=[],
                organization_id="org1",
                created_at=now,
                updated_at=now,
            ),
            ProductInDB(
                id="p2",
                name="Prod2",
                description="desc",
                unit_price=5,
                unit_cost=2,
                kind=ProductKind.REGULAR,
                tags=[],
                organization_id="org1",
                created_at=now,
                updated_at=now,
            ),
        ]

        mock_order_services = AsyncMock()
        mock_order_services.search_all_without_filters.return_value = [
            await self._order_with_products(
                "o1",
                [
                    StoredProduct(
                        product_id="p1",
                        name="Prod1",
                        unit_price=10,
                        unit_cost=6,
                        quantity=2,
                    ),
                    StoredProduct(
                        product_id="p2",
                        name="Prod2",
                        unit_price=5,
                        unit_cost=2,
                        quantity=1,
                    ),
                ],
                UTCDateTime(2024, 5, 1),
            ),
            await self._order_with_products(
                "o2",
                [
                    StoredProduct(
                        product_id="p1",
                        name="Prod1",
                        unit_price=10,
                        unit_cost=6,
                        quantity=1,
                    )
                ],
                UTCDateTime(2024, 5, 2),
            ),
        ]

        service = BillingServices(
            product_repository=product_repository,
            order_services=mock_order_services,
            fast_order_services=AsyncMock(),
            expenses_services=AsyncMock(),
        )

        products_profit = await service.get_products_profit(month=5, year=2024)

        self.assertEqual(len(products_profit), 2)
        self.assertEqual(products_profit[0].product_id, "p1")
        self.assertEqual(products_profit[0].total_profit, 12)
        self.assertEqual(products_profit[0].quantity, 3)
        self.assertEqual(products_profit[1].product_id, "p2")
        self.assertEqual(products_profit[1].total_profit, 3)
        self.assertEqual(products_profit[1].quantity, 1)

    @patch("app.crud.billing.services.RedisManager")
    @patch("app.crud.billing.services.get_plan_feature", new_callable=AsyncMock)
    async def test_get_daily_sales_sums_orders_by_day(self, mock_plan, mock_redis):
        mock_plan.return_value = SimpleNamespace(value="true")
        mock_redis.return_value.get_value.return_value = None

        mock_order_services = AsyncMock()
        mock_order_services.search_all_without_filters.return_value = [
            await self._order_with_products(
                "o1",
                [
                    StoredProduct(
                        product_id="p1",
                        name="Prod1",
                        unit_price=10,
                        unit_cost=5,
                        quantity=2,
                    )
                ],
                UTCDateTime(2024, 5, 1),
                additional=5,
                discount=2,
            ),
            await self._order_with_products(
                "o2",
                [
                    StoredProduct(
                        product_id="p2",
                        name="Prod2",
                        unit_price=15,
                        unit_cost=5,
                        quantity=1,
                    )
                ],
                UTCDateTime(2024, 5, 2),
            ),
        ]

        service = BillingServices(
            product_repository=AsyncMock(),
            order_services=mock_order_services,
            fast_order_services=AsyncMock(),
            expenses_services=AsyncMock(),
        )

        daily_sales = await service.get_daily_sales(month=5, year=2024)

        self.assertEqual(daily_sales[0].day, 1)
        self.assertEqual(daily_sales[0].total_amount, 23)
        self.assertEqual(daily_sales[1].day, 2)
        self.assertEqual(daily_sales[1].total_amount, 15)
        self.assertEqual(next(ds.total_amount for ds in daily_sales if ds.day == 3), 0)
