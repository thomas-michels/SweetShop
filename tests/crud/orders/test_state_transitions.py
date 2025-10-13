import pytest

from app.crud.orders.domain.order_state import OrderState
from app.crud.orders.schemas import OrderStatus


@pytest.mark.asyncio
async def test_state_transitions_allow_all_paths():
    state = OrderState(OrderStatus.PENDING)

    for status in OrderStatus:
        result = await state.transition_to(status)
        assert state.current_status == status
        assert result == status

    # Returning to a previous status should also be possible.
    result = await state.transition_to(OrderStatus.PENDING)
    assert state.current_status == OrderStatus.PENDING
    assert result == OrderStatus.PENDING


@pytest.mark.asyncio
async def test_transition_to_invalid_status_raises_value_error():
    state = OrderState(OrderStatus.PENDING)

    with pytest.raises(ValueError):
        await state.transition_to("INVALID")
