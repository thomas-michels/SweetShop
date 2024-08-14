from app.crud.products.repositories import ProductRepository
from app.crud.products.services import ProductServices


async def product_composer(
) -> ProductServices:
    product_repository = ProductRepository()
    product_services = ProductServices(product_repository=product_repository)
    return product_services
