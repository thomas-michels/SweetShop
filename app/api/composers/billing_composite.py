from fastapi import Depends
from app.api.composers.order_composite import order_composer
from app.api.composers.fast_order_composite import fast_order_composer
from app.api.composers.expense_composite import expense_composer
from app.crud.billing.services import BillingServices
from app.crud.expenses.services import ExpenseServices
from app.crud.fast_orders.services import FastOrderServices
from app.crud.orders.services import OrderServices
from app.crud.products.repositories import ProductRepository


async def billing_composer(
    order_services: OrderServices = Depends(order_composer),
    fast_order_services: FastOrderServices = Depends(fast_order_composer),
    expense_services: ExpenseServices = Depends(expense_composer)
) -> BillingServices:

    billing_services = BillingServices(
        product_repository=ProductRepository(order_services.organization_id),
        order_services=order_services,
        expenses_services=expense_services,
        fast_order_services=fast_order_services
    )
    return billing_services
