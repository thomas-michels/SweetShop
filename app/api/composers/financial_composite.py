from fastapi import Depends
from app.api.composers.order_composite import order_composer
from app.crud.financial.services import FinacialServices
from app.crud.orders.services import OrderServices


async def financial_composer(order_services: OrderServices = Depends(order_composer)) -> FinacialServices:
    financial_services = FinacialServices(order_services=order_services)
    return financial_services
