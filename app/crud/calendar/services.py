from datetime import datetime, timedelta
from typing import List, Tuple
from app.api.dependencies.get_plan_feature import get_plan_feature
from app.api.exceptions.authentication_exceptions import UnauthorizedException
from app.core.utils.features import Feature
from app.crud.orders.schemas import DeliveryType
from app.crud.orders.services import OrderServices

from .schemas import CalendarOrder


class CalendarServices:

    def __init__(
            self,
            order_services: OrderServices,
        ) -> None:
        self.order_services = order_services

    async def get_calendar(self, month: int, year: int, day: int = None) -> List[CalendarOrder]:
        plan_feature = await get_plan_feature(
            organization_id=self.order_services.organization_id,
            feature_name=Feature.DISPLAY_CALENDAR
        )

        if not plan_feature or not plan_feature.value.startswith("t"):
            raise UnauthorizedException(detail=f"You cannot access this feature")

        start_date, end_date = self.__get_start_and_end_date(month=month, year=year)

        orders = await self.order_services.search_all(
            customer_id=None,
            status=None,
            payment_status=[],
            delivery_type=None,
            start_date=start_date,
            end_date=end_date,
            tags=[],
            min_total_amount=None,
            max_total_amount=None,
            expand=["customers"],
            ignore_default_filters=True
        )

        calendars = []

        for order in orders:
            calendar_order = CalendarOrder(
                order_id=order.id,
                customer_name=order.customer.name if order.customer else "",
                order_date=order.order_date,
                order_status=order.status,
                order_delivery_type=order.delivery.delivery_type.value
            )

            if calendar_order.order_delivery_type == DeliveryType.DELIVERY:
                calendar_order.order_delivery_at = order.delivery.delivery_at
                calendar_order.address = order.delivery.address

            if day:
                if day == calendar_order.order_date.day:
                    calendars.append(calendar_order)

            else:
                calendars.append(calendar_order)

        return calendars

    def __get_start_and_end_date(self, month: int, year: int) -> Tuple[datetime, datetime]:
        start_date = datetime(year, month, 1)

        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(minutes=1)

        else:
            end_date = datetime(year, month + 1, 1) - timedelta(minutes=1)

        return start_date, end_date
