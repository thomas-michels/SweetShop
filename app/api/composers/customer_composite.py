from fastapi import Depends
from app.api.dependencies.get_current_organization import check_current_organization
from app.crud.customers.repositories import CustomerRepository
from app.crud.customers.services import CustomerServices


async def customer_composer(
    organization_id: str = Depends(check_current_organization)
) -> CustomerServices:
    customer_repository = CustomerRepository(organization_id=organization_id)
    customer_services = CustomerServices(customer_repository=customer_repository)
    return customer_services
