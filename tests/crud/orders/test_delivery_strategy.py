from datetime import datetime

import pytest

from app.crud.orders.domain.order import DeliveryData, Order, OrderData
from app.crud.orders.schemas import DeliveryType, OrderStatus
from app.crud.shared_schemas.payment import PaymentStatus


@pytest.fixture
def base_order_data() -> OrderData:
    return OrderData(
        id="ord_1",
        organization_id="org_1",
        status=OrderStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
        customer_id=None,
        products=[
            {
                "product_id": "prod_1",
                "name": "Cake",
                "unit_price": 10.0,
                "unit_cost": 5.0,
                "quantity": 2,
                "additionals": [
                    {
                        "item_id": "add_1",
                        "label": "Extra",
                        "unit_price": 1.5,
                        "unit_cost": 0.5,
                        "consumption_factor": 1.0,
                        "quantity": 1,
                    }
                ],
            }
        ],
        delivery=DeliveryData(delivery_type=DeliveryType.DELIVERY, delivery_value=5.0),
        additional=2.0,
        discount=1.0,
        tags=[],
        total_amount=0,
        order_date=datetime.utcnow(),
        preparation_date=datetime.utcnow(),
    )


def test_delivery_strategy_for_delivery(base_order_data: OrderData) -> None:
    order = Order(base_order_data)
    assert order.calculate_total() == 10 * 2 + 2 + (1.5 * 1 * 2) - 1 + 5


def test_delivery_strategy_for_withdrawal(base_order_data: OrderData) -> None:
    base_order_data.delivery = DeliveryData(delivery_type=DeliveryType.WITHDRAWAL)
    order = Order(base_order_data)
    assert order.calculate_total() == 10 * 2 + 2 + (1.5 * 1 * 2) - 1


def test_delivery_strategy_for_fast_order(base_order_data: OrderData) -> None:
    base_order_data.delivery = DeliveryData(delivery_type=DeliveryType.FAST_ORDER)
    order = Order(base_order_data)
    assert order.calculate_total() == 10 * 2 + 2 + (1.5 * 1 * 2) - 1
