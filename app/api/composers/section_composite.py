from fastapi import Depends
from app.api.dependencies.get_current_organization import check_current_organization
from app.crud.menus.repositories import MenuRepository
from app.crud.sections.repositories import SectionRepository
from app.crud.sections.services import SectionServices


async def section_composer(
    organization_id: str = Depends(check_current_organization)
) -> SectionServices:
    section_repository = SectionRepository(organization_id=organization_id)
    menu_repository = MenuRepository(organization_id=organization_id)

    section_services = SectionServices(
        section_repository=section_repository,
        menu_repository=menu_repository
    )
    return section_services
