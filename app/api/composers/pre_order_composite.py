from fastapi import Depends
from app.api.composers.message_composite import message_composer
from app.api.dependencies.get_current_organization import check_current_organization
from app.crud.customers.repositories import CustomerRepository
from app.crud.messages.services import MessageServices
from app.crud.offers.repositories import OfferRepository
from app.crud.organizations.repositories import OrganizationRepository
from app.crud.pre_orders.repositories import PreOrderRepository
from app.crud.pre_orders.services import PreOrderServices


async def pre_order_composer(
    organization_id: str = Depends(check_current_organization),
    message_services: MessageServices = Depends(message_composer)
) -> PreOrderServices:
    pre_order_repository = PreOrderRepository(organization_id=organization_id)
    customer_repository = CustomerRepository(organization_id=organization_id)
    offer_repository = OfferRepository(organization_id=organization_id)
    organization_repository = OrganizationRepository()

    pre_order_services = PreOrderServices(
        pre_order_repository=pre_order_repository,
        customer_repository=customer_repository,
        offer_repository=offer_repository,
        organization_repository=organization_repository,
        message_services=message_services
    )
    return pre_order_services
