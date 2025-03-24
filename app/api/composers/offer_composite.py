from fastapi import Depends
from app.api.dependencies.get_current_organization import check_current_organization
from app.crud.offers.repositories import OfferRepository
from app.crud.offers.services import OfferServices
from app.crud.products.repositories import ProductRepository
from app.crud.sections.repositories import SectionRepository


async def offer_composer(
    organization_id: str = Depends(check_current_organization)
) -> OfferServices:
    offer_repository = OfferRepository(organization_id=organization_id)
    section_repository = SectionRepository(organization_id=organization_id)
    product_repository = ProductRepository(organization_id=organization_id)

    offer_services = OfferServices(
        offer_repository=offer_repository,
        section_repository=section_repository,
        product_repository=product_repository
    )
    return offer_services
