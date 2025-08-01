from fastapi import Depends

from app.api.dependencies.get_current_organization import check_current_organization
from app.crud.product_additionals.repositories import ProductAdditionalRepository
from app.crud.product_additionals.services import ProductAdditionalServices
from app.crud.products.repositories import ProductRepository
from app.crud.additional_items.repositories import AdditionalItemRepository


async def product_additional_composer(
    organization_id: str = Depends(check_current_organization),
) -> ProductAdditionalServices:
    additional_repository = ProductAdditionalRepository(organization_id=organization_id)
    product_repository = ProductRepository(organization_id=organization_id)
    item_repository = AdditionalItemRepository(organization_id=organization_id)
    services = ProductAdditionalServices(
        additional_repository=additional_repository,
        product_repository=product_repository,
        item_repository=item_repository,
    )
    return services
