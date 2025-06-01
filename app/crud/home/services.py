import json
from typing import List

from app.api.dependencies.redis_manager import RedisManager
from app.api.exceptions.authentication_exceptions import UnauthorizedException
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.billing.services import BillingServices
from app.crud.calendar.schemas import CalendarOrder
from app.crud.calendar.services import CalendarServices
from app.crud.customers.services import CustomerServices
from app.crud.orders.services import OrderServices
from app.crud.products.services import ProductServices

from .schemas import HomeMetric, RecentOrder


class HomeServices:

    def __init__(
        self,
        order_services: OrderServices,
        product_services: ProductServices,
        customer_services: CustomerServices,
        calendar_services: CalendarServices,
        billing_services: BillingServices,
    ) -> None:
        self.order_services = order_services
        self.product_services = product_services
        self.customer_services = customer_services
        self.calendar_services = calendar_services
        self.billing_services = billing_services
        self.redis_manager = RedisManager()

    async def get_home_metrics(self) -> HomeMetric:
        key = f"metrics:organizations:{self.order_services.organization_id}"

        raw_metric = self.redis_manager.get_value(key=key)

        if raw_metric:
            raw_metric = json.loads(raw_metric)
            return HomeMetric(**raw_metric)

        home_metric = HomeMetric()
        now = UTCDateTime.now()

        orders = await self.__get_today_orders(now=now)

        total_amount = await self.__get_billing(now=now)

        recent_orders = await self.__get_recent_orders()

        home_metric.total_amount = total_amount
        home_metric.recent_orders = recent_orders
        home_metric.customers_count = await self.customer_services.search_count()
        home_metric.products_count = await self.product_services.search_count()
        home_metric.orders_today = len(orders)

        self.redis_manager.set_value(
            key=key, expiration=900, value=home_metric.model_dump_json()
        )

        return home_metric

    async def __get_recent_orders(self) -> List[RecentOrder]:
        orders = await self.order_services.search_recent(limit=3, expand=["customers"])

        recent_orders = []

        for order in orders:
            customer_name = (
                order.customer.name if order.customer else "Cliente não identificado"
            )

            recent_order = RecentOrder(
                order_id=order.id,
                customer_name=customer_name,
                total_amount=order.total_amount,
            )
            recent_orders.append(recent_order)

        return recent_orders

    async def __get_today_orders(self, now: UTCDateTime) -> List[CalendarOrder]:
        try:
            orders = await self.calendar_services.get_calendar(
                day=now.day, month=now.month, year=now.year
            )

            return orders if orders is not None else []

        except UnauthorizedException:
            return []

    async def __get_billing(self, now: UTCDateTime) -> float:
        try:
            billing = await self.billing_services.get_billing_for_dashboard(
                month=now.month, year=now.year
            )

            return billing.total_amount

        except UnauthorizedException:
            return 0
