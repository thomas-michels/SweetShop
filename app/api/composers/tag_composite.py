from fastapi import Depends
from app.api.dependencies.get_current_organization import check_current_organization
from app.crud.tags.repositories import TagRepository
from app.crud.tags.services import TagServices


async def tag_composer(
    organization_id: str = Depends(check_current_organization)
) -> TagServices:
    tag_repository = TagRepository(organization_id=organization_id)
    tag_services = TagServices(tag_repository=tag_repository)
    return tag_services
