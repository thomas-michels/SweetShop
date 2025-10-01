from datetime import date
from typing import List

from fastapi import APIRouter, Depends, Query, Request, Security, Response

from app.api.composers import expense_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.dependencies.pagination_parameters import pagination_parameters
from app.api.dependencies.paginator import Paginator
from app.api.dependencies.response import build_list_response
from app.api.shared_schemas.responses import MessageResponse
from app.crud.users import UserInDB
from app.crud.expenses import ExpenseServices
from .schemas import GetExpenseResponse, GetExpensesResponse

router = APIRouter(tags=["Expenses"])


@router.get(
    "/expenses/{expense_id}",
    responses={
        200: {"model": GetExpenseResponse},
        404: {"model": MessageResponse},
    },
)
async def get_expense_by_id(
    expense_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["expense:get"]),
    expense_services: ExpenseServices = Depends(expense_composer),
):
    expense_in_db = await expense_services.search_by_id(id=expense_id)

    if expense_in_db:
        return build_response(
            status_code=200, message="Expense found with success", data=expense_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Expense {expense_id} not found", data=None
        )


@router.get(
    "/expenses",
    responses={
        200: {"model": GetExpensesResponse},
        204: {"description": "No Content"},
    },
)
async def get_expenses(
    request: Request,
    query: str = Query(default=None),
    start_date: date | None = Query(default=None, alias="startDate"),
    end_date: date | None = Query(default=None, alias="endDate"),
    tags: List[str] = Query(default=[]),
    expand: List[str] = Query(default=[]),
    pagination: dict = Depends(pagination_parameters),
    current_user: UserInDB = Security(decode_jwt, scopes=["expense:get"]),
    expense_services: ExpenseServices = Depends(expense_composer),
):
    paginator = Paginator(
        request=request, pagination=pagination
    )

    total = await expense_services.search_count(
        query=query,
        start_date=start_date,
        end_date=end_date,
        tags=tags,
    )
    expenses = await expense_services.search_all(
        query=query,
        start_date=start_date,
        end_date=end_date,
        tags=tags,
        expand=expand,
        page=pagination["page"],
        page_size=pagination["page_size"],
    )

    paginator.set_total(total=total)

    if expenses:
        return build_list_response(
            status_code=200,
            message="Expenses found with success",
            pagination=paginator.pagination,
            data=expenses
        )

    else:
        return Response(status_code=204)
