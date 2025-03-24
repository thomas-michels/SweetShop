from fastapi import Depends
from app.api.dependencies.get_current_organization import check_current_organization
from app.crud.menus.repositories import MenuRepository
from app.crud.sections.repositories import SectionRepository
from app.crud.sections.services import SectionServices
from app.crud.offers.services import OfferServices
from app.api.composers.offer_composite import offer_composer


async def section_composer(
    organization_id: str = Depends(check_current_organization),
    offer_services: OfferServices = Depends(offer_composer),
) -> SectionServices:
    section_repository = SectionRepository(organization_id=organization_id)
    menu_repository = MenuRepository(organization_id=organization_id)

    section_services = SectionServices(
        section_repository=section_repository,
        menu_repository=menu_repository,
        offer_service=offer_services
    )
    return section_services
