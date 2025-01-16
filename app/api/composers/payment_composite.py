from fastapi import Depends
from app.api.dependencies.get_current_organization import check_current_organization
from app.crud.orders.repositories import OrderRepository
from app.crud.payments.repositories import PaymentRepository
from app.crud.payments.services import PaymentServices


async def payment_composer(
    organization_id: str = Depends(check_current_organization)
) -> PaymentServices:
    payment_repository = PaymentRepository(organization_id=organization_id)
    order_repository = OrderRepository(organization_id=organization_id)

    payment_services = PaymentServices(
        payment_repository=payment_repository,
        order_repository=order_repository
    )
    return payment_services
