from fastapi import APIRouter, Depends, Security

from app.api.composers import product_additional_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.product_additionals import (
    ProductAdditional,
    ProductAdditionalInDB,
    UpdateProductAdditional,
    AdditionalItem,
)
from app.crud.product_additionals.services import ProductAdditionalServices

router = APIRouter(tags=["ProductAdditionals"])


@router.post("/products/{product_id}/additionals", responses={201: {"model": ProductAdditionalInDB}})
async def create_product_additional(
    product_id: str,
    product_additional: ProductAdditional,
    current_user: UserInDB = Security(decode_jwt, scopes=["product_additional:create"]),
    product_additional_services: ProductAdditionalServices = Depends(product_additional_composer),
):
    additional_in_db = await product_additional_services.create(product_additional=product_additional)

    if additional_in_db:
        return build_response(
            status_code=201, message="ProductAdditional created with success", data=additional_in_db
        )
    else:
        return build_response(status_code=400, message="Erro ao criar adicional", data=None)


@router.put("/products/{product_id}/additionals/{additional_id}", responses={200: {"model": ProductAdditionalInDB}})
async def update_product_additional(
    product_id: str,
    additional_id: str,
    product_additional: UpdateProductAdditional,
    current_user: UserInDB = Security(decode_jwt, scopes=["product_additional:create"]),
    product_additional_services: ProductAdditionalServices = Depends(product_additional_composer),
):
    additional_in_db = await product_additional_services.update(id=additional_id, updated_product_additional=product_additional)

    if additional_in_db:
        return build_response(status_code=200, message="ProductAdditional updated with success", data=additional_in_db)
    else:
        return build_response(status_code=400, message="Erro ao atualizar adicional", data=None)


@router.delete("/products/{product_id}/additionals/{additional_id}", responses={200: {"model": ProductAdditionalInDB}})
async def delete_product_additional(
    product_id: str,
    additional_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["product_additional:delete"]),
    product_additional_services: ProductAdditionalServices = Depends(product_additional_composer),
):
    additional_in_db = await product_additional_services.delete_by_id(id=additional_id)

    if additional_in_db:
        return build_response(status_code=200, message="ProductAdditional deleted with success", data=additional_in_db)
    else:
        return build_response(status_code=404, message=f"ProductAdditional {additional_id} not found", data=None)


@router.post(
    "/products/{product_id}/additionals/{additional_id}/items",
    responses={200: {"model": ProductAdditionalInDB}},
)
async def add_additional_item(
    product_id: str,
    additional_id: str,
    item: AdditionalItem,
    current_user: UserInDB = Security(decode_jwt, scopes=["product_additional:create"]),
    product_additional_services: ProductAdditionalServices = Depends(product_additional_composer),
):
    additional_in_db = await product_additional_services.add_item(additional_id=additional_id, item=item)

    return build_response(
        status_code=200,
        message="Item created with success",
        data=additional_in_db,
    )


@router.put(
    "/products/{product_id}/additionals/{additional_id}/items/{item_id}",
    responses={200: {"model": ProductAdditionalInDB}},
)
async def update_additional_item(
    product_id: str,
    additional_id: str,
    item_id: str,
    item: AdditionalItem,
    current_user: UserInDB = Security(decode_jwt, scopes=["product_additional:create"]),
    product_additional_services: ProductAdditionalServices = Depends(product_additional_composer),
):
    additional_in_db = await product_additional_services.update_item(
        additional_id=additional_id, item_id=item_id, item=item
    )

    return build_response(
        status_code=200,
        message="Item updated with success",
        data=additional_in_db,
    )


@router.delete(
    "/products/{product_id}/additionals/{additional_id}/items/{item_id}",
    responses={200: {"model": ProductAdditionalInDB}},
)
async def delete_additional_item(
    product_id: str,
    additional_id: str,
    item_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["product_additional:delete"]),
    product_additional_services: ProductAdditionalServices = Depends(product_additional_composer),
):
    additional_in_db = await product_additional_services.delete_item(additional_id=additional_id, item_id=item_id)

    return build_response(
        status_code=200,
        message="Item deleted with success",
        data=additional_in_db,
    )
