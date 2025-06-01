from typing import List
from fastapi import APIRouter, Depends, Query, Response, Security
from app.api.composers import calendar_composer
from app.api.dependencies import build_response, decode_jwt
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.calendar import CalendarOrder, CalendarServices
from app.crud.users import UserInDB

router = APIRouter(tags=["Calendar"])


@router.get("/calendars", responses={200: {"model": List[CalendarOrder]}})
async def get_calendar(
    month_year: str = Query(
        default=f"{UTCDateTime.now().month}/{UTCDateTime.now().year}",
        pattern=r"\b(1[0-2]|0?[1-9])/([0-9]{4})\b",
        alias="monthYear",
    ),
    day: int | None = Query(default=None, example=9, gt=0, lt=32),
    current_user: UserInDB = Security(decode_jwt, scopes=["calendar:get"]),
    calendar_services: CalendarServices = Depends(calendar_composer),
):
    month = int(month_year.split("/")[0])
    year = int(month_year.split("/")[1])

    calendar_days = await calendar_services.get_calendar(
        month=month, year=year, day=day
    )

    if calendar_days:
        return build_response(
            status_code=200,
            message="Calendar days found with success",
            data=calendar_days,
        )

    else:
        return Response(status_code=204)
