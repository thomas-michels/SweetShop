from fastapi import Depends
from app.api.dependencies.get_current_organization import check_current_organization
from app.crud.menus.repositories import MenuRepository
from app.crud.menus.services import MenuServices


async def menu_composer(
    organization_id: str = Depends(check_current_organization)
) -> MenuServices:

    menu_repository = MenuRepository(organization_id=organization_id)
    menu_services = MenuServices(menu_repository=menu_repository)
    return menu_services
