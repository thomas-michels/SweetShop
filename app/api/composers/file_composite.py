from fastapi import Depends
from app.api.dependencies.get_current_organization import check_current_organization
from app.crud.files.repositories import FileRepository
from app.crud.files.services import FileServices


async def file_composer(
    organization_id: str = Depends(check_current_organization)
) -> FileServices:

    file_repository = FileRepository(organization_id=organization_id)
    file_services = FileServices(file_repository=file_repository)
    return file_services
