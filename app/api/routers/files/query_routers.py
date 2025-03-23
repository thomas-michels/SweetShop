from fastapi import APIRouter, Depends, Security

from app.api.composers import file_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.files import FileInDB, FileServices

router = APIRouter(tags=["Files"])


@router.get("/files/{file_id}", responses={200: {"model": FileInDB}})
async def get_file_by_id(
    file_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=[]),
    file_services: FileServices = Depends(file_composer),
):
    file_in_db = await file_services.search_by_id(id=file_id)

    if file_in_db:
        return build_response(
            status_code=200, message="File found with success", data=file_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"File {file_id} not found", data=None
        )
