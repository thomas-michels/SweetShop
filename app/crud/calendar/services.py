from datetime import date, datetime
from typing import List, Tuple
from app.api.dependencies.get_plan_feature import get_plan_feature
from app.api.exceptions.authentication_exceptions import UnauthorizedException
from app.core.utils.features import Feature
from app.crud.orders.services import OrderServices

from .schemas import Calendar, CalendarOrder


class CalendarServices:

    def __init__(
            self,
            order_services: OrderServices,
        ) -> None:
        self.order_services = order_services

    async def get_calendar(self, month: int, year: int, day: int = None) -> List[Calendar]:
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

        calendar_days = {}

        for order in orders:
            order_date = order.order_date.date()
            if order_date in calendar_days:
                calendar_day = calendar_days[order_date]

            else:
                calendar_day = Calendar(
                    month=month,
                    year=year,
                    day=order_date.day
                )
                calendar_days[order_date] = calendar_day

            calendar_order = CalendarOrder(
                order_id=order.id,
                customer_name=order.customer.name if order.customer else "",
                order_date=order.order_date,
                order_status=order.status,
                order_delivery_type=order.delivery.delivery_type.value
            )
            calendar_day.orders.append(calendar_order)

        if day:
            filtered_day = date(
                year=year,
                month=month,
                day=day
            )
            if calendar_days.get(filtered_day):
                return [calendar_days[filtered_day]]

            else:
                return None

        return list(calendar_days.values())

    def __get_start_and_end_date(self, month: int, year: int) -> Tuple[datetime, datetime]:
        start_date = datetime(year, month, 1)

        if month == 12:
            end_date = datetime(year + 1, 1, 1)

        else:
            end_date = datetime(year, month + 1, 1)

        return start_date,end_date
