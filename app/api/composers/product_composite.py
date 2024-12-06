from fastapi import Depends
from app.api.dependencies.get_current_organization import check_current_organization
from app.crud.products.repositories import ProductRepository
from app.crud.products.services import ProductServices


async def product_composer(
    organization_id: str = Depends(check_current_organization)
) -> ProductServices:
    product_repository = ProductRepository(organization_id=organization_id)
    product_services = ProductServices(product_repository=product_repository)
    return product_services
