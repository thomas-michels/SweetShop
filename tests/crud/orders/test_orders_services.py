import unittest
from unittest.mock import AsyncMock

from app.crud.orders.schemas import (
    OrderInDB,
    Delivery,
    DeliveryType,
    StoredProduct,
    OrderStatus,
    RequestedProduct,
    RequestedAdditionalItem,
    StoredAdditionalItem,
)
from app.crud.orders.services import OrderServices
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.shared_schemas.payment import PaymentStatus
from app.builder.order_calculator import OrderCalculator
from app.crud.products.schemas import ProductInDB, ProductKind
from app.crud.additional_items.schemas import AdditionalItemInDB


class TestOrderServices(unittest.IsolatedAsyncioTestCase):
    def _order_in_db(self):
        prod = StoredProduct(
            product_id="p1",
            name="Prod1",
            unit_price=2.0,
            unit_cost=1.0,
            quantity=1,
        )
        delivery = Delivery(delivery_type=DeliveryType.WITHDRAWAL)
        now = UTCDateTime.now()
        return OrderInDB(
            id="ord1",
            organization_id="org1",
            customer_id=None,
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            products=[prod],
            tags=["tag1"],
            delivery=delivery,
            preparation_date=now,
            order_date=now,
            description=None,
            additional=0,
            discount=0,
            total_amount=2.0,
            tax=0,
            payments=[],
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    async def test_search_by_id(self):
        mock_repo = AsyncMock()
        mock_repo.select_by_id.return_value = self._order_in_db()
        service = OrderServices(
            order_repository=mock_repo,
            product_repository=AsyncMock(),
            tag_repository=AsyncMock(),
            customer_repository=AsyncMock(),
            organization_repository=AsyncMock(),
            additional_item_repository=AsyncMock(),
        )
        result = await service.search_by_id(id="ord1")
        self.assertEqual(result.id, "ord1")
        mock_repo.select_by_id.assert_awaited_with(id="ord1")

    async def test_search_count(self):
        mock_repo = AsyncMock()
        mock_repo.select_count.return_value = 4
        service = OrderServices(
            order_repository=mock_repo,
            product_repository=AsyncMock(),
            tag_repository=AsyncMock(),
            customer_repository=AsyncMock(),
            organization_repository=AsyncMock(),
            additional_item_repository=AsyncMock(),
        )
        count = await service.search_count(
            status=None,
            payment_status=[],
            delivery_type=None,
            customer_id=None,
            start_date=None,
            end_date=None,
            tags=None,
            min_total_amount=None,
            max_total_amount=None,
        )
        self.assertEqual(count, 4)
        mock_repo.select_count.assert_awaited()

    async def test_search_all(self):
        mock_repo = AsyncMock()
        mock_repo.select_all.return_value = [self._order_in_db()]
        service = OrderServices(
            order_repository=mock_repo,
            product_repository=AsyncMock(),
            tag_repository=AsyncMock(),
            customer_repository=AsyncMock(),
            organization_repository=AsyncMock(),
            additional_item_repository=AsyncMock(),
        )
        results = await service.search_all(
            status=None,
            payment_status=[],
            delivery_type=None,
            customer_id=None,
            start_date=None,
            end_date=None,
            tags=None,
            min_total_amount=None,
            max_total_amount=None,
            expand=[],
        )
        self.assertEqual(len(results), 1)
        mock_repo.select_all.assert_awaited()

    async def test_validate_products_with_additionals(self):
        product_repo = AsyncMock()
        product_repo.select_by_id.return_value = ProductInDB(
            id="p1",
            organization_id="org1",
            name="Prod1",
            description="desc",
            unit_price=2.0,
            unit_cost=1.0,
            kind=ProductKind.REGULAR,
            tags=[],
            file_id=None,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )
        additional_repo = AsyncMock()
        additional_repo.select_by_id.return_value = AdditionalItemInDB(
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

        service = OrderServices(
            order_repository=AsyncMock(),
            product_repository=product_repo,
            tag_repository=AsyncMock(),
            customer_repository=AsyncMock(),
            organization_repository=AsyncMock(),
            additional_item_repository=additional_repo,
        )

        raw_product = RequestedProduct(
            product_id="p1",
            quantity=1,
            additionals=[RequestedAdditionalItem(item_id="a1", quantity=1)],
        )

        products = await service._OrderServices__validate_products(raw_products=[raw_product])

        self.assertEqual(products[0].additionals[0].label, "Extra")
        additional_repo.select_by_id.assert_awaited_with(id="a1")

    async def test_order_calculator_with_additionals(self):
        product_repo = AsyncMock()
        product_repo.select_by_id.return_value = ProductInDB(
            id="p1",
            organization_id="org1",
            name="Prod1",
            description="desc",
            unit_price=2.0,
            unit_cost=1.0,
            kind=ProductKind.REGULAR,
            tags=[],
            file_id=None,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )

        calc = OrderCalculator(product_repository=product_repo)
        additional = StoredAdditionalItem(
            item_id="a1",
            quantity=1,
            label="Extra",
            unit_price=1.0,
            unit_cost=0.5,
            consumption_factor=1.0,
        )
        prod = StoredProduct(
            product_id="p1",
            name="Prod1",
            unit_price=2.0,
            unit_cost=1.0,
            quantity=2,
            additionals=[additional],
        )
        total = await calc.calculate(
            delivery_value=0, additional=0, discount=0, products=[prod]
        )

        self.assertEqual(total, 6.0)
