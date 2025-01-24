from datetime import date
from typing import List

from fastapi import APIRouter, Depends, Query, Security, Response

from app.api.composers import expense_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.dependencies.bucket import S3BucketManager
from app.crud.users import UserInDB
from app.crud.expenses import ExpenseInDB, ExpenseServices

router = APIRouter(tags=["Images"])


@router.get("/images/{expense_id}", responses={200: {"model": ExpenseInDB}})
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


@router.get("/images", responses={200: {"model": List[ExpenseInDB]}})
async def get_images(
    query: str = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=["expense:get"]),
    # expense_services: ExpenseServices = Depends(expense_composer),
):
    bucket = S3BucketManager()
    files = bucket.list_files()

    # images = await expense_services.search_all(
    #     query=query,
    #     start_date=start_date,
    #     end_date=end_date,
    #     expand=expand
    # )

    if files:
        return build_response(
            status_code=200, message="Images found with success", data=files
        )

    else:
        return Response(status_code=204)
