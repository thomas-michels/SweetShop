from fastapi import Depends
from app.api.dependencies.get_current_organization import check_current_organization
from app.crud.files.repositories import FileRepository
from app.crud.tags.repositories import TagRepository
from app.crud.products.repositories import ProductRepository
from app.crud.products.services import ProductServices
from app.crud.product_additionals.services import ProductAdditionalServices
from app.crud.product_additionals.repositories import ProductAdditionalRepository
from app.crud.additional_items.repositories import AdditionalItemRepository


async def product_composer(
    organization_id: str = Depends(check_current_organization)
) -> ProductServices:
    tag_repository = TagRepository(organization_id=organization_id)
    product_repository = ProductRepository(organization_id=organization_id)
    file_repository = FileRepository(organization_id=organization_id)
    product_additional_repository = ProductAdditionalRepository(organization_id=organization_id)
    product_additional_services = ProductAdditionalServices(
        additional_repository=product_additional_repository,
        product_repository=product_repository,
        item_repository=AdditionalItemRepository(organization_id=organization_id),
    )
    product_services = ProductServices(
        product_repository=product_repository,
        tag_repository=tag_repository,
        file_repository=file_repository,
        additional_services=product_additional_services,
    )
    return product_services
