from fastapi import Depends
from app.api.dependencies.get_current_organization import check_current_organization
from app.crud.files.repositories import FileRepository
from app.crud.offers.repositories import OfferRepository
from app.crud.products.repositories import ProductRepository
from app.crud.offers.services import OfferServices
from app.crud.section_offers.repositories import SectionOfferRepository


async def offer_composer(
    organization_id: str = Depends(check_current_organization)
) -> OfferServices:
    offer_repository = OfferRepository(organization_id=organization_id)
    product_repository = ProductRepository(organization_id=organization_id)
    file_repository = FileRepository(organization_id=organization_id)
    section_offer_repository = SectionOfferRepository(organization_id=organization_id)

    offer_services = OfferServices(
        offer_repository=offer_repository,
        product_repository=product_repository,
        file_repository=file_repository,
        section_offer_repository=section_offer_repository,
    )
    return offer_services
