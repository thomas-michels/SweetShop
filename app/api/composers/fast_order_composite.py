from fastapi import Depends
from app.api.dependencies.get_current_organization import check_current_organization
from app.crud.fast_orders.repositories import FastOrderRepository
from app.crud.fast_orders.services import FastOrderServices
from app.crud.products.repositories import ProductRepository


async def fast_order_composer(
    organization_id: str = Depends(check_current_organization)
) -> FastOrderServices:
    fast_order_repository = FastOrderRepository(organization_id=organization_id)
    product_repository = ProductRepository(organization_id=organization_id)

    fast_order_services = FastOrderServices(
        fast_order_repository=fast_order_repository,
        product_repository=product_repository,
    )
    return fast_order_services
