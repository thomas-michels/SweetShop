from fastapi import Depends
from app.api.dependencies.get_current_organization import check_current_organization
from app.crud.files.repositories import FileRepository
from app.crud.offers.repositories import OfferRepository
from app.crud.products.repositories import ProductRepository
from app.crud.offers.services import OfferServices
from app.crud.section_items.repositories import SectionItemRepository


async def offer_composer(
    organization_id: str = Depends(check_current_organization)
) -> OfferServices:
    offer_repository = OfferRepository(organization_id=organization_id)
    product_repository = ProductRepository(organization_id=organization_id)
    file_repository = FileRepository(organization_id=organization_id)
    section_item_repository = SectionItemRepository(organization_id=organization_id)

    offer_services = OfferServices(
        offer_repository=offer_repository,
        product_repository=product_repository,
        file_repository=file_repository,
        section_item_repository=section_item_repository,
    )
    return offer_services
