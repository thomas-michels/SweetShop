from app.crud.tags.repositories import TagRepository
from app.crud.tags.services import TagServices


async def tag_composer() -> TagServices:
    tag_repository = TagRepository(organization_id="org_123")
    tag_services = TagServices(tag_repository=tag_repository)
    return tag_services
