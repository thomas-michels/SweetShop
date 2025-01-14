from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Query, Security, Response

from app.api.composers import billing_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.billing import BillingServices, Billing

router = APIRouter(tags=["Billing"])


@router.get("/billings/dashboard", responses={200: {"model": List[Billing]}})
async def get_dashboard_billings(
    month_year: str = Query(
        default=f"{datetime.now().month}/{datetime.now().year}",
        pattern=r'\b(1[0-2]|0?[1-9])/([0-9]{4})\b',
        alias="monthYear"
    ),
    current_user: UserInDB = Security(decode_jwt, scopes=["billing:get"]),
    billing_services: BillingServices = Depends(billing_composer),
):
    month = int(month_year.split("/")[0])
    year = int(month_year.split("/")[1])

    billings = await billing_services.get_billing_for_dashboard(
        month=month,
        year=year
    )

    if billings:
        return build_response(
            status_code=200, message="Billings for dashboard found with success", data=billings
        )

    else:
        return Response(status_code=204)


@router.get("/billings/monthly", responses={200: {"model": List[Billing]}})
async def get_monthly_billings(
    last_months: int = Query(gt=0, lt=13, default=3, alias="lastMonths"),
    current_user: UserInDB = Security(decode_jwt, scopes=["billing:get"]),
    billing_services: BillingServices = Depends(billing_composer),
):
    billings = await billing_services.get_monthly_billings(
        last_months=last_months
    )

    if billings:
        return build_response(
            status_code=200, message="Monthly Billings found with success", data=billings
        )

    else:
        return Response(status_code=204)


@router.get("/billings/products", responses={200: {"model": List[Billing]}})
async def get_best_selling_products(
    month_year: str = Query(
        default=f"{datetime.now().month}/{datetime.now().year}",
        pattern=r'\b(1[0-2]|0?[1-9])/([0-9]{4})\b',
        alias="monthYear"
    ),
    current_user: UserInDB = Security(decode_jwt, scopes=["billing:get"]),
    billing_services: BillingServices = Depends(billing_composer),
):
    month = int(month_year.split("/")[0])
    year = int(month_year.split("/")[1])

    selling_products = await billing_services.get_best_selling_products(
        month=month,
        year=year
    )

    if selling_products:
        return build_response(
            status_code=200, message="Best selling products found with success", data=selling_products
        )

    else:
        return Response(status_code=204)


@router.get("/billings/expenses/categories", responses={200: {"model": List[Billing]}})
async def get_expanses_categories(
    month_year: str = Query(
        default=f"{datetime.now().month}/{datetime.now().year}",
        pattern=r'\b(1[0-2]|0?[1-9])/([0-9]{4})\b',
        alias="monthYear"
    ),
    current_user: UserInDB = Security(decode_jwt, scopes=["billing:get"]),
    billing_services: BillingServices = Depends(billing_composer),
):
    month = int(month_year.split("/")[0])
    year = int(month_year.split("/")[1])

    expanses_categories = await billing_services.get_expanses_categories(
        month=month,
        year=year
    )

    if expanses_categories:
        return build_response(
            status_code=200, message="Expanses categories found with success", data=expanses_categories
        )

    else:
        return Response(status_code=204)
