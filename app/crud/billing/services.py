from typing import List
from app.crud.expenses.services import ExpenseServices
from app.crud.fast_orders.services import FastOrderServices
from app.crud.orders.services import OrderServices
from app.crud.shared_schemas.payment import Payment, PaymentMethod

from .schemas import Billing


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

    async def search_by_month(self, month: int) -> Billing:
        orders = await self.order_services.search_all(
            customer_id=None,
            status=None,
            payment_status=None,
            delivery_type=None,
            month=month,
            expand=[],
        )

        fast_orders = await self.fast_order_services.search_all(
            expand=[]
        )
        orders.extend(fast_orders)

        billing = Billing(month=month)

        for order in orders:
            billing.total_amount += order.total_amount
            total_paid = 0

            self.__process_payments(
                billing=billing,
                payment_details=order.payment_details,
                total_paid=total_paid,
                total_amount=order.total_amount
            )

        return billing

    def __process_payments(
            self,
            billing: Billing,
            payment_details: List[Payment],
            total_paid: float,
            total_amount: float
        ) -> None:

        for payment in payment_details:
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
