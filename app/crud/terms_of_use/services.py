import hashlib
import os
from datetime import datetime
from typing import List

from fastapi import UploadFile
from tempfile import NamedTemporaryFile
from app.api.dependencies.bucket import S3BucketManager
from app.api.exceptions.authentication_exceptions import BadRequestException
from app.api.shared_schemas.terms_of_use import FilterTermOfUse
from app.crud.terms_of_use.term_of_use_acceptance_repositories import TermOfUseAcceptanceRepository

from .schemas import TermOfUse, TermOfUseAcceptance, TermOfUseAcceptanceInDB, TermOfUseInDB
from .term_of_use_repositories import TermOfUseRepository


class TermOfUseServices:

    def __init__(
            self,
            term_of_use_repository: TermOfUseRepository,
            acceptance_repository: TermOfUseAcceptanceRepository,
        ) -> None:
        self.__term_of_use_repository = term_of_use_repository
        self.__acceptance_repository = acceptance_repository
        self.__bucket = S3BucketManager(mode="public")

    async def create_term_of_use(self, version: str, file: UploadFile) -> TermOfUseInDB:
        file_content = await file.read()
        file_hash = hashlib.sha256(file_content).hexdigest()

        if await self.__term_of_use_repository.select_by_hash(hash=file_hash):
            raise BadRequestException(detail="This term of use already exists")

        with NamedTemporaryFile(mode="+wb", suffix=".pdf", delete=False) as buffer:
            buffer.write(file_content)
            buffer.flush()

        file_url = self.__bucket.upload_file(
            local_path=buffer.name,
            bucket_path=f"documents/terms_of_use_{version}.pdf"
        )

        os.remove(buffer.name)

        term_of_use = TermOfUse(
            version=version,
            hash=file_hash,
            url=file_url
        )

        term_of_use_in_db = await self.__term_of_use_repository.create(
            term_of_use=term_of_use
        )

        return term_of_use_in_db

    async def search_term_of_use_by_id(self, id: str) -> TermOfUseInDB:
        term_of_use_in_db = await self.__term_of_use_repository.select_by_id(id=id)
        return term_of_use_in_db

    async def search_term_of_use_all(self, filter: FilterTermOfUse) -> List[TermOfUseInDB]:
        term_of_uses = await self.__term_of_use_repository.select_all()

        if filter == FilterTermOfUse.ALL:
            return term_of_uses

        elif filter == FilterTermOfUse.LATEST:
            return [term_of_uses[0]] if term_of_uses else []

    async def delete_term_of_use_by_id(self, id: str) -> TermOfUseInDB:
        term_of_use_in_db = await self.__term_of_use_repository.delete_by_id(id=id)
        return term_of_use_in_db

    async def accept_term_of_use(self, acceptance: TermOfUseAcceptance) -> TermOfUseAcceptanceInDB:
        term_of_use = await self.__term_of_use_repository.select_by_id(id=acceptance.term_of_use_id)

        if await self.__acceptance_repository.select_by_term_and_user(
            term_of_use_id=acceptance.term_of_use_id,
            user_id=acceptance.user_id
        ):
            raise BadRequestException(detail="Term of use already accepted")

        acceptance.extra_data["term_of_use_version"] = term_of_use.version
        acceptance.extra_data["term_of_use_hash"] = term_of_use.hash

        acceptance_in_db = await self.__acceptance_repository.create(
            term_of_use_acceptance=acceptance
        )

        return acceptance_in_db

    async def search_acceptance_by_id(self, term_of_use_id: str, user_id: str) -> TermOfUseAcceptanceInDB:
        acceptance_in_db = await self.__acceptance_repository.select_by_term_and_user(
            term_of_use_id=term_of_use_id,
            user_id=user_id
        )
        return acceptance_in_db

    async def delete_acceptance(self, term_of_use_id: str, user_id: str) -> TermOfUseAcceptanceInDB:
        acceptance_in_db = await self.__acceptance_repository.select_by_term_and_user(
            term_of_use_id=term_of_use_id,
            user_id=user_id
        )

        if not acceptance_in_db:
            return

        now = int(datetime.now().timestamp())

        acceptance_in_db.extra_data["deleted_at"] = now
        acceptance_in_db.extra_data["deleted_by"] = user_id

        acceptance_in_db = await self.__acceptance_repository.delete(
            acceptance=acceptance_in_db
        )

        return acceptance_in_db
