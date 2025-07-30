from fastapi import Depends

from app.api.dependencies.get_current_organization import check_current_organization
from app.crud.sections.repositories import SectionRepository
from app.crud.offers.repositories import OfferRepository
from app.crud.section_offers.repositories import SectionOfferRepository
from app.crud.section_offers.services import SectionOfferServices


async def section_offer_composer(
    organization_id: str = Depends(check_current_organization),
) -> SectionOfferServices:
    section_offer_repository = SectionOfferRepository(organization_id=organization_id)
    section_repository = SectionRepository(organization_id=organization_id)
    offer_repository = OfferRepository(organization_id=organization_id)

    services = SectionOfferServices(
        section_offer_repository=section_offer_repository,
        section_repository=section_repository,
        offer_repository=offer_repository,
    )
    return services
