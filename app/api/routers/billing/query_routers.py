from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Query, Security, Response

from app.api.composers import billing_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.billing import BillingServices, Billing

router = APIRouter(tags=["Billing"])


@router.get("/billings", responses={200: {"model": List[Billing]}})
async def get_billings(
    month: int = Query(gt=0, lt=13, default=datetime.now().month),
    current_user: UserInDB = Security(decode_jwt, scopes=["billing:get"]),
    billing_services: BillingServices = Depends(billing_composer),
):
    billings = await billing_services.search_by_month(
        month=month
    )

    if billings:
        return build_response(
            status_code=200, message="Billings found with success", data=billings
        )

    else:
        return Response(status_code=204)
