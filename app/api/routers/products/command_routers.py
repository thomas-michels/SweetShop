from fastapi import APIRouter, Depends, Security

from app.api.composers import product_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.products import Product, ProductInDB, UpdateProduct, ProductServices

router = APIRouter(tags=["Products"])


@router.post("/products", responses={201: {"model": ProductInDB}})
async def create_products(
    product: Product,
    current_user: UserInDB = Security(decode_jwt, scopes=["product:create"]),
    product_services: ProductServices = Depends(product_composer),
):
    product_in_db = await product_services.create(
        product=product
    )

    return build_response(
        status_code=201, message="Product created with success", data=product_in_db
    )


@router.put("/product/{product_id}", responses={200: {"model": ProductInDB}})
async def update_product(
    product_id: str,
    product: UpdateProduct,
    current_user: UserInDB = Security(decode_jwt, scopes=["product:update"]),
    product_services: ProductServices = Depends(product_composer),
):
    product_in_db = await product_services.update(id=product_id, updated_product=product)

    return build_response(
        status_code=200, message="Product updated with success", data=product_in_db
    )


@router.delete("/product/{product_id}", responses={200: {"model": ProductInDB}})
async def delete_product(
    product_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["product:delete"]),
    product_services: ProductServices = Depends(product_composer),
):
    product_in_db = await product_services.delete_by_id(id=product_id)

    return build_response(
        status_code=200, message="Product deleted with success", data=product_in_db
    )
