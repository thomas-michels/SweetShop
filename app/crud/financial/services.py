from typing import List
from .schemas import Financial
from app.crud.orders.services import OrderServices


class FinacialServices:

    def __init__(self, order_services: OrderServices) -> None:
        self.order_services = order_services

    async def search_by_month(self, month: int) -> List[Financial]:
        orders = await self.order_services.search_all(
            customer_id=None,
            expand=[],
            status=None
        )

        financials = []

        for order in orders:
            financials.append(Financial(
                order_id=order.id,
                order_date=order.created_at,
                payment_status=order.payment_status,
                value=order.value
            ))

        return financials
