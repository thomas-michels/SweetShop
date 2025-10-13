from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.crud.orders.schemas import (
    CompleteOrder,
    Delivery,
    DeliveryType,
    OrderInDB,
    OrderStatus,
    StoredProduct,
    UpdateOrder,
)
from app.crud.orders.services.order_facade import OrderFacade
from app.crud.shared_schemas.payment import PaymentStatus
from app.core.utils.utc_datetime import UTCDateTime


@pytest.mark.asyncio
async def test_order_facade_updates_status_and_persists_changes():
    delivery = Delivery(delivery_type=DeliveryType.WITHDRAWAL)
    stored_product = StoredProduct(
        product_id="prod_1",
        name="Cake",
        unit_price=10.0,
        unit_cost=5.0,
        quantity=1,
        observation=None,
        additionals=[],
    )

    original_order = OrderInDB(
        id="ord_1",
        organization_id="org_1",
        customer_id="cust_1",
        status=OrderStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
        products=[stored_product],
        tags=[],
        delivery=delivery,
        preparation_date=UTCDateTime.now(),
        order_date=UTCDateTime.now(),
        description=None,
        additional=0,
        discount=0,
        reason_id=None,
        total_amount=10.0,
        payments=[],
        tax=0,
        is_active=True,
        created_at=UTCDateTime.now(),
        updated_at=UTCDateTime.now(),
    )

    updated_order_db = original_order.model_copy(update={"status": OrderStatus.SCHEDULED})
    complete_order = CompleteOrder(
        **updated_order_db.model_dump(),
        customer=None,
        tags=[],
    )

    order_repository = SimpleNamespace(
        organization_id="org_1",
        select_by_id=AsyncMock(return_value=original_order),
        select_count_by_date=AsyncMock(return_value=0),
        select_count=AsyncMock(return_value=0),
        select_all=AsyncMock(return_value=[]),
        select_all_without_filters=AsyncMock(return_value=[]),
        select_recent=AsyncMock(return_value=[]),
        create=AsyncMock(),
        update=AsyncMock(return_value=updated_order_db),
        delete_by_id=AsyncMock(return_value=original_order),
    )

    product_repository = SimpleNamespace(select_by_id=AsyncMock())
    tag_repository = SimpleNamespace(select_by_id=AsyncMock(return_value=None))
    customer_repository = SimpleNamespace(
        select_by_id=AsyncMock(return_value=None),
        select_by_ids=AsyncMock(return_value=[]),
    )
    organization_repository = SimpleNamespace(
        select_by_id=AsyncMock(return_value=SimpleNamespace(
            tax=0,
            enable_order_notifications=False,
            international_code="55",
            ddd="11",
            phone_number="999999999",
        ))
    )
    additional_item_repository = SimpleNamespace(select_by_id=AsyncMock())
    product_additional_repository = SimpleNamespace(select_by_product_id=AsyncMock(return_value=[]))
    message_services = SimpleNamespace(create=AsyncMock())

    facade = OrderFacade(
        order_repository=order_repository,
        product_repository=product_repository,
        tag_repository=tag_repository,
        customer_repository=customer_repository,
        organization_repository=organization_repository,
        additional_item_repository=additional_item_repository,
        product_additional_repository=product_additional_repository,
        message_services=message_services,
    )

    facade.search_by_id = AsyncMock(return_value=original_order)  # type: ignore[attr-defined]
    facade._OrderFacade__order_calculator.calculate = AsyncMock(return_value=10.0)  # type: ignore[attr-defined]
    facade._OrderFacade__build_complete_order = AsyncMock(return_value=complete_order)  # type: ignore[attr-defined]

    update_payload = UpdateOrder(status=OrderStatus.SCHEDULED)

    result = await facade.update("ord_1", update_payload)

    order_repository.update.assert_awaited_once()
    awaited_call = order_repository.update.await_args  # type: ignore[attr-defined]
    assert awaited_call.kwargs["order_id"] == "ord_1"
    assert awaited_call.kwargs["order"]["status"] == OrderStatus.SCHEDULED.value
    assert result == complete_order
