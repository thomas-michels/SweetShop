from typing import List

from fastapi import APIRouter, Depends, Query, Request, Security, Response

from app.api.composers import menu_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.dependencies.pagination_parameters import pagination_parameters
from app.api.dependencies.paginator import Paginator
from app.api.dependencies.response import build_list_response
from app.crud.users import UserInDB
from app.crud.menus import MenuInDB, MenuServices

router = APIRouter(tags=["Menus"])


@router.get("/menus/{menu_id}", responses={200: {"model": MenuInDB}})
async def get_menu_by_id(
    menu_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=[]),
    menu_services: MenuServices = Depends(menu_composer),
):
    menu_in_db = await menu_services.search_by_id(id=menu_id)

    if menu_in_db:
        return build_response(
            status_code=200, message="Menu found with success", data=menu_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Menu {menu_id} not found", data=None
        )


@router.get("/menus", responses={200: {"model": List[MenuInDB]}})
async def get_menus(
    request: Request,
    query: str = Query(default=None),
    expand: List[str] = Query(default=[]),
    pagination: dict = Depends(pagination_parameters),
    current_user: UserInDB = Security(decode_jwt, scopes=[]),
    menu_services: MenuServices = Depends(menu_composer),
):
    paginator = Paginator(
        request=request, pagination=pagination
    )

    total = await menu_services.search_count(query=query)

    menus = await menu_services.search_all(
        query=query,
        expand=expand,
        page=pagination["page"],
        page_size=pagination["page_size"]
    )

    paginator.set_total(total=total)

    if menus:
        return build_list_response(
            status_code=200,
            message="Menus found with success",
            pagination=paginator.pagination,
            data=menus
        )

    else:
        return Response(status_code=204)
