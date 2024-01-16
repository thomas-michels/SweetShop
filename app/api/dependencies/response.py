from typing import List
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import status
from pydantic import BaseModel
from app.api.shared_schemas.responses import MessageResponse, Response


def build_response(status_code: status, message: str, data: BaseModel | List[BaseModel]) -> JSONResponse:
    if data:
        raw_response = Response(
            message=message,
            data=data
        )

    else:
        raw_response = MessageResponse(
            message=message
        )

    return JSONResponse(
        content=jsonable_encoder(raw_response.model_dump()),
        status_code=status_code
    )
