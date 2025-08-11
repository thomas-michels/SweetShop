from typing import List

from pydantic import Field, ConfigDict

from app.api.shared_schemas.responses import Response, ListResponseSchema
from app.crud.products.schemas import ProductInDB

EXAMPLE_PRODUCT = {
    "id": "pro_123",
    "name": "Brigadeiro",
    "description": "Brigadeiro de Leite Ninho",
    "unit_price": 1.5,
    "unit_cost": 0.75,
    "kind": "REGULAR",
    "tags": ["doce"],
    "file_id": "fil_123",
    "organization_id": "org_123",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}


class GetProductResponse(Response):
    data: ProductInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Product found with success",
                "data": EXAMPLE_PRODUCT,
            }
        }
    )


class GetProductsResponse(ListResponseSchema):
    data: List[ProductInDB] = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Products found with success",
                "pagination": {"page": 1, "page_size": 2, "total": 2},
                "data": [
                    EXAMPLE_PRODUCT,
                    {**EXAMPLE_PRODUCT, "id": "pro_456", "name": "Coxinha"},
                ],
            }
        }
    )


class GetProductsCountResponse(Response):
    data: int | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Products count found with success",
                "data": 2,
            }
        }
    )


class CreateProductResponse(Response):
    data: ProductInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Product created with success",
                "data": EXAMPLE_PRODUCT,
            }
        }
    )


class UpdateProductResponse(Response):
    data: ProductInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Product updated with success",
                "data": EXAMPLE_PRODUCT,
            }
        }
    )


class DeleteProductResponse(Response):
    data: ProductInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Product deleted with success",
                "data": EXAMPLE_PRODUCT,
            }
        }
    )
