from fastapi import APIRouter, Depends, Security

from app.api.composers import product_composer, offer_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.products import Product, ProductInDB, UpdateProduct, ProductServices
from app.crud.offers.services import OfferServices

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

    if product_in_db:
        return build_response(
            status_code=201, message="Product created with success", data=product_in_db
        )

    else:
        return build_response(
            status_code=400, message="Erro ao criar produto", data=None
        )


@router.put("/products/{product_id}", responses={200: {"model": ProductInDB}})
async def update_product(
    product_id: str,
    product: UpdateProduct,
    current_user: UserInDB = Security(decode_jwt, scopes=["product:create"]),
    product_services: ProductServices = Depends(product_composer),
    offer_services: OfferServices = Depends(offer_composer),
):
    product_in_db = await product_services.update(id=product_id, updated_product=product)

    if product_in_db:
        await offer_services.update_product_in_offers(product=product_in_db)
        return build_response(
            status_code=200, message="Product updated with success", data=product_in_db
        )

    else:
        return build_response(
            status_code=400, message="Erro ao atualizar produto", data=None
        )


@router.delete("/products/{product_id}", responses={200: {"model": ProductInDB}})
async def delete_product(
    product_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["product:delete"]),
    product_services: ProductServices = Depends(product_composer),
):
    product_in_db = await product_services.delete_by_id(id=product_id)

    if product_in_db:
        return build_response(
            status_code=200, message="Product deleted with success", data=product_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Produto {product_id} não encontrado", data=None
        )
