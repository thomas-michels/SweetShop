from fastapi import APIRouter, Depends, Query, Response, Security

from app.api.composers import business_day_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.business_days import BusinessDayServices
from app.crud.users import UserInDB

from .schemas import GetBusinessDayResponse

router = APIRouter(tags=["Business Days"])


@router.get(
    "/business_day",
    responses={
        200: {"model": GetBusinessDayResponse},
        204: {"description": "Business day not found"},
    },
)
async def get_business_day(
    menu_id: str = Query(alias="menuId"),
    current_user: UserInDB = Security(decode_jwt, scopes=["business_day:get"]),
    business_day_services: BusinessDayServices = Depends(business_day_composer),
):
    business_day = await business_day_services.get_today(menu_id=menu_id)

    if business_day:
        return build_response(
            status_code=200,
            message="Business day found with success",
            data=business_day,
        )

    return Response(status_code=204)
