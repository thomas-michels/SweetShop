from fastapi import Depends
from app.api.composers.billing_composite import billing_composer
from app.api.composers.calendar_composite import calendar_composer
from app.api.composers.customer_composite import customer_composer
from app.api.composers.order_composite import order_composer
from app.api.composers.product_composite import product_composer
from app.crud.billing.services import BillingServices
from app.crud.calendar.services import CalendarServices
from app.crud.customers.services import CustomerServices
from app.crud.metrics.services import MetricServices
from app.crud.orders.services import OrderServices
from app.crud.products.services import ProductServices


async def metric_composer(
    order_services: OrderServices = Depends(order_composer),
    calendar_services: CalendarServices = Depends(calendar_composer),
    customer_services: CustomerServices = Depends(customer_composer),
    product_services: ProductServices = Depends(product_composer),
    billing_services: BillingServices = Depends(billing_composer),
) -> MetricServices:

    metric_services = MetricServices(
        order_services=order_services,
        calendar_services=calendar_services,
        customer_services=customer_services,
        product_services=product_services,
        billing_services=billing_services
    )
    return metric_services
