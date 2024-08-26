from app.crud.orders.repositories import OrderRepository
from app.crud.orders.services import OrderServices
from app.crud.products.repositories import ProductRepository


async def order_composer(
) -> OrderRepository:
    order_repository = OrderRepository()
    product_repository = ProductRepository()
    order_services = OrderServices(
        order_repository=order_repository,
        product_repository=product_repository
    )
    return order_services
