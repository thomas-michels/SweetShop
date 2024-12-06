from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Query, Security, Response

from app.api.composers import financial_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.financial import FinacialServices, Financial

router = APIRouter(tags=["Financial"])


@router.get("/financials", responses={200: {"model": List[Financial]}})
async def get_financials(
    month: int = Query(gt=0, lt=13, default=datetime.now().month),
    current_user: UserInDB = Security(decode_jwt, scopes=["financial:get"]),
    financial_services: FinacialServices = Depends(financial_composer),
):
    financials = await financial_services.search_by_month(
        month=month
    )

    if financials:
        return build_response(
            status_code=200, message="Financials found with success", data=financials
        )

    else:
        return Response(status_code=204)


# @router.get("/customers", responses={200: {"model": List[CustomerInDB]}})
# async def get_customers(
#     query: str = Query(default=None),
#     current_customer: UserInDB = Security(decode_jwt, scopes=["customer:get"]),
#     customer_services: CustomerServices = Depends(customer_composer),
# ):
#     customers = await customer_services.search_all(query=query)

#     if customers:
#         return build_response(
#             status_code=200, message="Customers found with success", data=customers
#         )

#     else:
#         return Response(status_code=204)
