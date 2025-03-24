from fastapi import APIRouter, Depends, Security

from app.api.composers import menu_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.menus import Menu, MenuInDB, UpdateMenu, MenuServices

router = APIRouter(tags=["Menus"])


@router.post("/menus", responses={201: {"model": MenuInDB}})
async def create_menu(
    menu: Menu,
    current_user: UserInDB = Security(decode_jwt, scopes=["menu:create"]),
    menu_services: MenuServices = Depends(menu_composer),
):
    menu_in_db = await menu_services.create(
        menu=menu
    )

    if menu_in_db:
        return build_response(
            status_code=201, message="Menu created with success", data=menu_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on create a menu", data=None
        )


@router.put("/menus/{menu_id}", responses={200: {"model": MenuInDB}})
async def update_menu(
    menu_id: str,
    menu: UpdateMenu,
    current_user: UserInDB = Security(decode_jwt, scopes=["menu:create"]),
    menu_services: MenuServices = Depends(menu_composer),
):
    menu_in_db = await menu_services.update(id=menu_id, updated_menu=menu)

    if menu_in_db:
        return build_response(
            status_code=200, message="Menu updated with success", data=menu_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on update a menu", data=None
        )


@router.delete("/menus/{menu_id}", responses={200: {"model": MenuInDB}})
async def delete_menu(
    menu_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["menu:delete"]),
    menu_services: MenuServices = Depends(menu_composer),
):
    menu_in_db = await menu_services.delete_by_id(id=menu_id)

    if menu_in_db:
        return build_response(
            status_code=200, message="Menu deleted with success", data=menu_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Menu {menu_id} not found", data=None
        )
