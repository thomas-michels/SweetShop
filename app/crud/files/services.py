import os
from uuid import uuid4

from tempfile import NamedTemporaryFile

from fastapi import UploadFile
from app.api.dependencies.bucket import S3BucketManager
from app.api.exceptions.authentication_exceptions import BadRequestException
from app.core.utils.image_validator import validate_image_file
from app.core.utils.resize_image import resize_image
from .schemas import File, FileInDB, FilePurpose
from .repositories import FileRepository


class FileServices:

    def __init__(
            self,
            file_repository: FileRepository,
        ) -> None:
        self.__file_repository = file_repository
        self.__s3_manager = S3BucketManager(mode="private")

    async def create(self, purpose: FilePurpose, file: UploadFile) -> FileInDB:
        file_id = str(uuid4())

        if purpose == FilePurpose.PRODUCT:
            validated_file = await self.validate_image(file=file, size=(400, 400))

        elif purpose == FilePurpose.ORGANIZATION:
            validated_file = await self.validate_image(file=file, size=(80, 80))

        else:
            raise BadRequestException(detail="Purpose not recognized")

        file_extension = validated_file.filename.split(".")[-1]

        with NamedTemporaryFile(mode="wb", suffix=f".{file_extension}", delete=False) as buffer:
            buffer.write(await validated_file.read())
            buffer.flush()

        file_url = self.__s3_manager.upload_file(
            local_path=buffer.name,
            bucket_path=f"organization/{self.__file_repository.organization_id}/files/{file_id}.{file_extension}"
        )

        os.remove(buffer.name)

        file_schema = File(
            purpose=purpose,
            type=file_extension,
            url=file_url
        )

        file_in_db = await self.__file_repository.create(
            file=file_schema
        )

        return file_in_db

    async def search_by_id(self, id: str) -> FileInDB:
        file_in_db = await self.__file_repository.select_by_id(id=id)
        return file_in_db

    async def delete_by_id(self, id: str) -> FileInDB:
        file_in_db = await self.__file_repository.delete_by_id(id=id)
        return file_in_db

    async def validate_image(self, file: UploadFile, size: tuple):
        image_type = await validate_image_file(image=file)

        file_image = await resize_image(
            upload_image=file,
            size=size
        )

        return file_image
