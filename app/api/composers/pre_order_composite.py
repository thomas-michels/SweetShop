from fastapi import Depends
from app.api.dependencies.get_current_organization import check_current_organization
from app.crud.customers.repositories import CustomerRepository
from app.crud.pre_orders.repositories import PreOrderRepository
from app.crud.pre_orders.services import PreOrderServices


async def pre_order_composer(
    organization_id: str = Depends(check_current_organization)
) -> PreOrderServices:
    pre_order_repository = PreOrderRepository(organization_id=organization_id)
    customer_repository = CustomerRepository(organization_id=organization_id)

    pre_order_services = PreOrderServices(
        pre_order_repository=pre_order_repository,
        customer_repository=customer_repository
    )
    return pre_order_services
