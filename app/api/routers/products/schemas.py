from typing import List

from pydantic import Field, ConfigDict

from app.api.shared_schemas.responses import Response, ListResponseSchema
from app.crud.products.schemas import ProductInDB, CompleteProduct

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

EXAMPLE_COMPLETE_PRODUCT = {
    **EXAMPLE_PRODUCT,
    "tags": [{"id": "tag_123", "name": "Doce", "organization_id": "org_123"}],
    "file": {
        "id": "fil_123",
        "key": "brigadeiro.png",
        "url": "http://localhost/brigadeiro.png",
        "organization_id": "org_123",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    },
    "additionals": [
        {
            "id": "pad_123",
            "name": "Coberturas",
            "selection_type": "RADIO",
            "min_quantity": 0,
            "max_quantity": 1,
            "position": 1,
            "items": [
                {
                    "position": 1,
                    "product_id": "pro_456",
                    "label": "Granulado",
                    "unit_price": 0.5,
                    "unit_cost": 0.2,
                    "consumption_factor": 1,
                }
            ],
            "organization_id": "org_123",
            "product_id": "pro_123",
        }
    ],
}


class GetProductResponse(Response):
    data: CompleteProduct | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Product found with success",
                "data": EXAMPLE_COMPLETE_PRODUCT,
            }
        }
    )


class GetProductsResponse(ListResponseSchema):
    data: List[CompleteProduct] = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Products found with success",
                "pagination": {"page": 1, "page_size": 2, "total": 2},
                "data": [
                    EXAMPLE_COMPLETE_PRODUCT,
                    {**EXAMPLE_COMPLETE_PRODUCT, "id": "pro_456", "name": "Coxinha"},
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
