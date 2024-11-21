from app.crud.customers.repositories import CustomerRepository
from app.crud.orders.repositories import OrderRepository
from app.crud.orders.services import OrderServices
from app.crud.products.repositories import ProductRepository
from app.crud.tags.repositories import TagRepository


async def order_composer(
) -> OrderRepository:
    order_repository = OrderRepository()
    product_repository = ProductRepository()
    tag_repository = TagRepository(organization_id="org_123")
    customer_repository = CustomerRepository()

    order_services = OrderServices(
        order_repository=order_repository,
        product_repository=product_repository,
        tag_repository=tag_repository,
        customer_repository=customer_repository
    )
    return order_services
