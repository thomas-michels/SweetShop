from fastapi import Depends
from app.api.composers.order_composite import order_composer
from app.crud.calendar.services import CalendarServices
from app.crud.orders.services import OrderServices


async def calendar_composer(
    order_services: OrderServices = Depends(order_composer),
) -> CalendarServices:

    calendar_services = CalendarServices(
        order_services=order_services,
    )
    return calendar_services
