from fastapi import Depends

from app.api.dependencies.get_current_organization import check_current_organization
from app.api.composers import offer_composer, product_composer
from app.crud.sections.repositories import SectionRepository
from app.crud.section_items.repositories import SectionItemRepository
from app.crud.section_items.services import SectionItemServices


async def section_item_composer(
    organization_id: str = Depends(check_current_organization),
    offer_service = Depends(offer_composer),
    product_service = Depends(product_composer),
) -> SectionItemServices:
    section_item_repository = SectionItemRepository(organization_id=organization_id)
    section_repository = SectionRepository(organization_id=organization_id)

    services = SectionItemServices(
        section_item_repository=section_item_repository,
        section_repository=section_repository,
        offer_service=offer_service,
        product_service=product_service,
    )
    return services
