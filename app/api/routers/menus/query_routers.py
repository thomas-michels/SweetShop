from typing import List

from fastapi import APIRouter, Depends, Query, Security, Response

from app.api.composers import menu_composer
from app.api.dependencies import build_response, decode_jwt
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
    query: str = Query(default=None),
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=[]),
    menu_services: MenuServices = Depends(menu_composer),
):
    menus = await menu_services.search_all(
        query=query,
        expand=expand
    )

    if menus:
        return build_response(
            status_code=200, message="Menus found with success", data=menus
        )

    else:
        return Response(status_code=204)
