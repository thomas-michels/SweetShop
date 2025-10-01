from fastapi import APIRouter, Depends, Security

from app.api.composers import business_day_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.shared_schemas.responses import MessageResponse
from app.crud.business_days import BusinessDayServices, UpsertBusinessDay
from app.crud.users import UserInDB

from .schemas import UpsertBusinessDayResponse

router = APIRouter(tags=["Business Days"])


@router.put(
    "/business_day",
    responses={
        200: {"model": UpsertBusinessDayResponse},
        400: {"model": MessageResponse},
    },
)
async def upsert_business_day(
    business_day: UpsertBusinessDay,
    current_user: UserInDB = Security(decode_jwt, scopes=["business_day:update"]),
    business_day_services: BusinessDayServices = Depends(business_day_composer),
):
    business_day_in_db = await business_day_services.upsert_today(
        business_day=business_day
    )

    if business_day_in_db:
        return build_response(
            status_code=200,
            message="Business day saved with success",
            data=business_day_in_db,
        )

    return build_response(
        status_code=400,
        message="Some error happened on save business day",
        data=None,
    )
