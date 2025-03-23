from fastapi import APIRouter, Depends, Form, Security, UploadFile

from app.api.composers import file_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.files.services import FileServices
from app.crud.users import UserInDB
from app.crud.files.schemas import FileInDB, FilePurpose

router = APIRouter(tags=["Files"])


@router.post("/files", responses={201: {"model": FileInDB}})
async def create_file(
    file: UploadFile,
    purpose: FilePurpose = Form(example=FilePurpose.PRODUCT),
    current_user: UserInDB = Security(decode_jwt, scopes=["file:create"]),
    file_services: FileServices = Depends(file_composer),
):
    file_in_db = await file_services.create(
        purpose=purpose,
        file=file
    )

    if file_in_db:
        return build_response(
            status_code=201, message="File created with success", data=file_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on create file", data=None
        )


@router.delete("/files/{file_id}", responses={200: {"model": FileInDB}})
async def delete_file(
    file_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["file:delete"]),
    file_services: FileServices = Depends(file_composer),
):
    file_in_db = await file_services.delete_by_id(
        id=file_id
    )

    if file_in_db:
        return build_response(
            status_code=200, message="File deleted with success", data=file_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on delete file", data=None
        )
