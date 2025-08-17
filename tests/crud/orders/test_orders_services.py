import unittest
from unittest.mock import AsyncMock, patch

from app.crud.orders.schemas import (
    OrderInDB,
    Delivery,
    DeliveryType,
    StoredProduct,
    OrderStatus,
    RequestedProduct,
    RequestedAdditionalItem,
    StoredAdditionalItem,
    RequestOrder,
)
from app.crud.orders.services import OrderServices
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.shared_schemas.payment import PaymentStatus
from app.builder.order_calculator import OrderCalculator
from app.crud.products.schemas import ProductInDB, ProductKind
from app.crud.additional_items.schemas import AdditionalItemInDB
from app.crud.product_additionals.schemas import ProductAdditionalInDB, OptionKind
from app.crud.customers.schemas import CustomerInDB
from app.api.exceptions.authentication_exceptions import BadRequestException


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
            product_additional_repository=AsyncMock(),
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
            product_additional_repository=AsyncMock(),
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
            product_additional_repository=AsyncMock(),
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

    async def test_search_all_without_filters_prefetches_customers(self):
        order1 = self._order_in_db()
        order1.id = "ord1"
        order1.customer_id = "c1"
        order2 = self._order_in_db()
        order2.id = "ord2"
        order2.customer_id = "c2"

        order_repo = AsyncMock()
        order_repo.select_all_without_filters.return_value = [order1, order2]

        customer_repo = AsyncMock()

        customers = [
            CustomerInDB(
                id="c1",
                name="Alice",
                international_code="55",
                ddd="047",
                phone_number="111111111",
                addresses=[],
                tags=[],
                organization_id="org1",
                is_active=True,
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
            ),
            CustomerInDB(
                id="c2",
                name="Bob",
                international_code="55",
                ddd="047",
                phone_number="222222222",
                addresses=[],
                tags=[],
                organization_id="org1",
                is_active=True,
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
            ),
        ]

        customer_repo.select_by_ids.return_value = customers

        service = OrderServices(
            order_repository=order_repo,
            product_repository=AsyncMock(),
            tag_repository=AsyncMock(),
            customer_repository=customer_repo,
            organization_repository=AsyncMock(),
            additional_item_repository=AsyncMock(),
            product_additional_repository=AsyncMock(),
        )

        start = UTCDateTime.now()
        end = UTCDateTime.now()

        results = await service.search_all_without_filters(
            start_date=start,
            end_date=end,
            expand=["customers"],
        )

        self.assertEqual(len(results), 2)
        customer_repo.select_by_ids.assert_awaited_once()
        customer_repo.select_by_id.assert_not_called()

    async def test_search_recent_prefetches_customers(self):
        order1 = self._order_in_db()
        order1.id = "ord1"
        order1.customer_id = "c1"
        order2 = self._order_in_db()
        order2.id = "ord2"
        order2.customer_id = "c2"

        order_repo = AsyncMock()
        order_repo.select_recent.return_value = [order1, order2]

        customer_repo = AsyncMock()

        customers = [
            CustomerInDB(
                id="c1",
                name="Alice",
                international_code="55",
                ddd="047",
                phone_number="111111111",
                addresses=[],
                tags=[],
                organization_id="org1",
                is_active=True,
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
            ),
            CustomerInDB(
                id="c2",
                name="Bob",
                international_code="55",
                ddd="047",
                phone_number="222222222",
                addresses=[],
                tags=[],
                organization_id="org1",
                is_active=True,
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
            ),
        ]

        customer_repo.select_by_ids.return_value = customers

        service = OrderServices(
            order_repository=order_repo,
            product_repository=AsyncMock(),
            tag_repository=AsyncMock(),
            customer_repository=customer_repo,
            organization_repository=AsyncMock(),
            additional_item_repository=AsyncMock(),
            product_additional_repository=AsyncMock(),
        )

        results = await service.search_recent(limit=2, expand=["customers"])

        self.assertEqual(len(results), 2)
        customer_repo.select_by_ids.assert_awaited_once()
        customer_repo.select_by_id.assert_not_called()

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
        product_additional_repo = AsyncMock()
        product_additional_repo.select_by_product_id.return_value = [
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

        service = OrderServices(
            order_repository=AsyncMock(),
            product_repository=product_repo,
            tag_repository=AsyncMock(),
            customer_repository=AsyncMock(),
            organization_repository=AsyncMock(),
            additional_item_repository=additional_repo,
            product_additional_repository=product_additional_repo,
        )

        raw_product = RequestedProduct(
            product_id="p1",
            quantity=1,
            additionals=[RequestedAdditionalItem(item_id="a1", quantity=1)],
        )

        products = await service._OrderServices__validate_products(raw_products=[raw_product])

        self.assertEqual(products[0].additionals[0].label, "Extra")
        self.assertEqual(products[0].unit_price, 3.0)
        self.assertEqual(products[0].unit_cost, 1.5)
        additional_repo.select_by_id.assert_awaited_with(id="a1")
        product_additional_repo.select_by_product_id.assert_awaited_with(product_id="p1")

    async def test_validate_products_max_quantity(self):
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
        product_additional_repo = AsyncMock()
        product_additional_repo.select_by_product_id.return_value = [
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

        service = OrderServices(
            order_repository=AsyncMock(),
            product_repository=product_repo,
            tag_repository=AsyncMock(),
            customer_repository=AsyncMock(),
            organization_repository=AsyncMock(),
            additional_item_repository=additional_repo,
            product_additional_repository=product_additional_repo,
        )

        raw_product = RequestedProduct(
            product_id="p1",
            quantity=1,
            additionals=[RequestedAdditionalItem(item_id="a1", quantity=2)],
        )

        with self.assertRaises(BadRequestException):
            await service._OrderServices__validate_products(raw_products=[raw_product])

    async def test_order_calculator_with_additionals(self):
        product_repo = AsyncMock()
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
            unit_price=3.0,
            unit_cost=1.5,
            quantity=2,
            additionals=[additional],
        )
        total = await calc.calculate(
            delivery_value=0, additional=0, discount=0, products=[prod]
        )

        self.assertEqual(total, 6.0)

    async def test_create_includes_additionals_in_product_value(self):
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

        product_additional_repo = AsyncMock()
        product_additional_repo.select_by_product_id.return_value = [
            ProductAdditionalInDB(
                id="add1",
                organization_id="org1",
                product_id="p1",
                name="Group",
                selection_type=OptionKind.CHECKBOX,
                min_quantity=0,
                max_quantity=2,
                position=1,
                items=[],
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
            )
        ]

        order_repo = AsyncMock()
        stored_additional = StoredAdditionalItem(
            item_id="a1",
            quantity=1,
            label="Extra",
            unit_price=1.0,
            unit_cost=0.5,
            consumption_factor=1.0,
        )
        stored_product = StoredProduct(
            product_id="p1",
            name="Prod1",
            unit_price=3.0,
            unit_cost=1.5,
            quantity=1,
            additionals=[stored_additional],
        )
        now = UTCDateTime.now()
        order_repo.create.return_value = OrderInDB(
            id="ord1",
            organization_id="org1",
            customer_id=None,
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            products=[stored_product],
            tags=[],
            delivery=Delivery(delivery_type=DeliveryType.WITHDRAWAL),
            preparation_date=now,
            order_date=now,
            description=None,
            additional=0,
            discount=0,
            total_amount=3.0,
            tax=0,
            payments=[],
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        organization_repo = AsyncMock()
        organization_repo.select_by_id.return_value = type("Org", (), {"tax": 0})()

        service = OrderServices(
            order_repository=order_repo,
            product_repository=product_repo,
            tag_repository=AsyncMock(),
            customer_repository=AsyncMock(),
            organization_repository=organization_repo,
            additional_item_repository=additional_repo,
            product_additional_repository=product_additional_repo,
        )

        req_order = RequestOrder(
            customer_id=None,
            status=OrderStatus.PENDING,
            products=[RequestedProduct(product_id="p1", quantity=1, additionals=[RequestedAdditionalItem(item_id="a1", quantity=1)])],
            tags=[],
            delivery=Delivery(delivery_type=DeliveryType.WITHDRAWAL),
            preparation_date=now,
            order_date=now,
            description=None,
            additional=0,
            discount=0,
            reason_id=None,
        )

        with patch(
            "app.crud.orders.services.get_plan_feature",
            AsyncMock(return_value=type("PF", (), {"value": "-"})()),
        ):
            await service.create(req_order)

        created_order = order_repo.create.await_args.kwargs["order"]
        self.assertEqual(created_order.additional, 0)
        self.assertEqual(created_order.products[0].unit_price, 3.0)
