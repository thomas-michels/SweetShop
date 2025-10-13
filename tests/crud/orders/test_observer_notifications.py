from datetime import datetime
import pytest

from app.crud.orders.domain.events import OrderEvent
from app.crud.orders.domain.observers import OrderObserver
from app.crud.orders.domain.order import DeliveryData, Order, OrderData
from app.crud.orders.schemas import DeliveryType, OrderStatus
from app.crud.shared_schemas.payment import PaymentStatus


class DummyObserver(OrderObserver):
    def __init__(self) -> None:
        self.events: list[tuple[OrderEvent, dict]] = []

    async def update(self, order: Order, event: OrderEvent, **context: object) -> None:
        self.events.append((event, context))


@pytest.mark.asyncio
async def test_observer_receives_status_change_event():
    order_data = OrderData(
        id="ord_1",
        organization_id="org_1",
        status=OrderStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
        customer_id=None,
        products=[],
        delivery=DeliveryData(delivery_type=DeliveryType.WITHDRAWAL),
        additional=0,
        discount=0,
        tags=[],
        total_amount=0,
        order_date=datetime.utcnow(),
        preparation_date=datetime.utcnow(),
    )

    order = Order(order_data)
    observer = DummyObserver()
    order.attach(observer)

    await order.change_status(OrderStatus.DONE)

    assert observer.events
    event, context = observer.events[0]
    assert event == OrderEvent.STATUS_CHANGED
    assert context["old_status"] == OrderStatus.PENDING
    assert context["new_status"] == OrderStatus.DONE
