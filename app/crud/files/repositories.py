from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository
from app.core.utils.utc_datetime import UTCDateTime

from .models import FileModel
from .schemas import File, FileInDB

_logger = get_logger(__name__)


class FileRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.organization_id = organization_id

    async def create(self, file: File) -> FileInDB:
        try:
            file_model = FileModel(
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
                organization_id=self.organization_id,
                **file.model_dump(),
            )

            file_model.save()
            _logger.info(
                f"File {file.url} saved for organization {self.organization_id}"
            )

            return FileInDB.model_validate(file_model)

        except Exception as error:
            _logger.error(f"Error on create_file: {str(error)}")
            raise UnprocessableEntity(message="Error on create new file")

    async def select_by_id(self, id: str, raise_404: bool = True) -> FileInDB:
        try:
            file_model: FileModel = FileModel.objects(
                id=id, is_active=True, organization_id=self.organization_id
            ).first()

            if file_model:
                return FileInDB.model_validate(file_model)

            if raise_404:
                raise NotFoundError(message=f"File #{id} not found")

        except Exception as error:
            if raise_404:
                _logger.error(f"Error on select_by_id: {str(error)}")
                raise NotFoundError(message=f"File #{id} not found")

    async def delete_by_id(self, id: str, raise_404: bool = True) -> FileInDB:
        try:
            file_model: FileModel = FileModel.objects(
                id=id, is_active=True, organization_id=self.organization_id
            ).first()
            file_model.delete(soft_delete=False)

            return FileInDB.model_validate(file_model)

        except Exception as error:
            if raise_404:
                _logger.error(f"Error on delete_by_id: {str(error)}")
                raise NotFoundError(message=f"File #{id} not found")
