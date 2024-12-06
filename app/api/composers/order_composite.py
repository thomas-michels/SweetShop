from fastapi import Depends
from app.api.dependencies.get_current_organization import check_current_organization
from app.crud.customers.repositories import CustomerRepository
from app.crud.orders.repositories import OrderRepository
from app.crud.orders.services import OrderServices
from app.crud.products.repositories import ProductRepository
from app.crud.tags.repositories import TagRepository


async def order_composer(
    organization_id: str = Depends(check_current_organization)
) -> OrderServices:
    order_repository = OrderRepository(organization_id=organization_id)
    product_repository = ProductRepository(organization_id=organization_id)
    tag_repository = TagRepository(organization_id=organization_id)
    customer_repository = CustomerRepository(organization_id=organization_id)

    order_services = OrderServices(
        order_repository=order_repository,
        product_repository=product_repository,
        tag_repository=tag_repository,
        customer_repository=customer_repository
    )
    return order_services
