from datetime import datetime
from typing import Dict, List, Tuple
from app.api.dependencies.get_plan_feature import get_plan_feature
from app.api.exceptions.authentication_exceptions import UnauthorizedException
from app.core.utils.features import Feature
from app.crud.expenses.services import ExpenseServices
from app.crud.fast_orders.services import FastOrderServices
from app.crud.orders.schemas import PaymentInOrder
from app.crud.orders.services import OrderServices
from app.crud.shared_schemas.payment import PaymentMethod

from .schemas import BestPlace, Billing, ExpanseCategory, SellingProduct


class BillingServices:

    def __init__(
            self,
            order_services: OrderServices,
            fast_order_services: FastOrderServices,
            expenses_services: ExpenseServices,
        ) -> None:
        self.order_services = order_services
        self.fast_order_services = fast_order_services
        self.expenses_services = expenses_services

    async def get_billing_for_dashboard(self, month: int, year: int) -> Billing:
        plan_feature = await get_plan_feature(
            organization_id=self.order_services.organization_id,
            feature_name=Feature.DISPLAY_DASHBOARD
        )

        if not plan_feature.value.startswith("t"):
            raise UnauthorizedException(detail=f"You cannot access this feature")

        return await self.__generate_monthly_billing(month=month, year=year)

    async def get_monthly_billings(self, last_months: int) -> List[Billing]:
        plan_feature = await get_plan_feature(
            organization_id=self.order_services.organization_id,
            feature_name=Feature.DISPLAY_DASHBOARD
        )

        if not plan_feature.value.startswith("t"):
            raise UnauthorizedException(detail=f"You cannot access this feature")

        billings = []

        for i in range(last_months):
            year, month = self.__get_month_and_year(past_months=i)

            billing = await self.__generate_monthly_billing(month=month, year=year)
            billings.append(billing)

        return billings

    async def get_best_selling_products(self, month: int, year: int) -> List[SellingProduct]:
        plan_feature = await get_plan_feature(
            organization_id=self.order_services.organization_id,
            feature_name=Feature.DISPLAY_DASHBOARD
        )

        if not plan_feature.value.startswith("t"):
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
            expand=[],
        )

        fast_orders = await self.fast_order_services.search_all(
            expand=[],
            start_date=start_date,
            end_date=end_date
        )

        orders.extend(fast_orders)

        selling_products: Dict[str, SellingProduct] = {}

        for order in orders:
            for order_product in order.products:
                if order_product.product_id not in selling_products:
                    selling_products[order_product.product_id] = SellingProduct(
                        product_id=order_product.product_id,
                        product_name=order_product.name
                    )

                product_category = selling_products[order_product.product_id]
                product_category.quantity += 1

        selling_products = list(selling_products.values())

        selling_products.sort(key=lambda c: c.quantity, reverse=True)

        return selling_products[:5]

    async def get_expanses_categories(self, month: int, year: int) -> List[ExpanseCategory]:
        plan_feature = await get_plan_feature(
            organization_id=self.order_services.organization_id,
            feature_name=Feature.DISPLAY_DASHBOARD
        )

        if not plan_feature.value.startswith("t"):
            raise UnauthorizedException(detail=f"You cannot access this feature")

        start_date, end_date = self.__get_start_and_end_date(month=month, year=year)

        expenses = await self.expenses_services.search_all(
            start_date=start_date,
            end_date=end_date,
            query=None,
            expand=["tags"]
        )

        categories: Dict[str, ExpanseCategory] = {}

        for expense in expenses:
            for tag in expense.tags:
                if tag.id not in categories:
                    categories[tag.id] = ExpanseCategory(
                        tag_id=tag.id,
                        tag_name=tag.name
                    )

                category = categories[tag.id]

                category.total_paid += expense.total_paid

        category_list = list(categories.values())

        category_list.sort(key=lambda c: c.total_paid, reverse=True)

        return category_list[:5]

    async def get_best_places(self, month: int, year: int) -> List[BestPlace]:
        plan_feature = await get_plan_feature(
            organization_id=self.order_services.organization_id,
            feature_name=Feature.DISPLAY_DASHBOARD
        )

        if not plan_feature.value.startswith("t"):
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
            expand=["tags"],
        )

        places: Dict[str, BestPlace] = {}

        for order in orders:
            for tag in order.tags:
                if tag.id not in places:
                    places[tag.id] = BestPlace(
                        tag_id=tag.id,
                        tag_name=tag.name
                    )

                place = places[tag.id]
                place.total_amount += order.total_amount

        places_list = list(places.values())

        places_list.sort(key=lambda c: c.total_amount, reverse=True)

        return places_list[:5]

    def __get_month_and_year(self, past_months: int) -> Tuple[int, int]:
        current_date = datetime.now()

        year = current_date.year
        month = current_date.month - past_months

        while month <= 0:
            month += 12
            year -= 1

        return year, month

    async def __generate_monthly_billing(self, month: int, year: int) -> Billing:
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
            expand=[],
        )

        fast_orders = await self.fast_order_services.search_all(
            expand=[],
            start_date=start_date,
            end_date=end_date
        )

        expenses = await self.expenses_services.search_all(
            start_date=start_date,
            end_date=end_date,
            query=None,
            expand=[]
        )

        orders.extend(fast_orders)

        billing = Billing(month=month, year=year)

        for order in orders:
            billing.total_amount += order.total_amount
            total_paid = 0

            self.__process_payments(
                billing=billing,
                payments=order.payments,
                total_paid=total_paid,
                total_amount=order.total_amount
            )

        for expense in expenses:
            billing.total_expanses += expense.total_paid

        billing.round_numbers()
        return billing

    def __process_payments(
            self,
            billing: Billing,
            payments: List[PaymentInOrder],
            total_paid: float,
            total_amount: float
        ) -> None:

        for payment in payments:
            total_paid += payment.amount
            billing.payment_received += payment.amount

            if payment.method == PaymentMethod.CASH:
                billing.cash_received += payment.amount

            elif payment.method == PaymentMethod.PIX:
                billing.pix_received += payment.amount

            elif payment.method == PaymentMethod.CREDIT_CARD:
                billing.credit_card_received += payment.amount

            elif payment.method == PaymentMethod.DEBIT_CARD:
                billing.debit_card_received += payment.amount

        if total_paid < total_amount:
            billing.pending_payments += round((total_amount - total_paid), 2)

    def __get_start_and_end_date(self, month: int, year: int) -> Tuple[datetime, datetime]:
        start_date = datetime(year, month, 1)

        if month == 12:
            end_date = datetime(year + 1, 1, 1)

        else:
            end_date = datetime(year, month + 1, 1)

        return start_date,end_date
