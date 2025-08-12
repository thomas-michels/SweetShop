from typing import List

from pydantic import Field, ConfigDict

from app.api.shared_schemas.responses import Response, ListResponseSchema
from app.crud.offers import OfferInDB

EXAMPLE_OFFER = {
    "id": "off_123",
    "name": "Doces",
    "description": "Bolos e tortas",
    "unit_price": 12.0,
    "is_visible": True,
    "products": [
        {
            "product_id": "prod_123",
            "name": "Cake",
            "description": "Chocolate cake",
            "unit_cost": 10.0,
            "unit_price": 15.0,
            "quantity": 1,
            "file_id": "file_123",
        }
    ],
    "organization_id": "org_123",
}


class GetOfferResponse(Response):
    data: OfferInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"message": "Offer found with success", "data": EXAMPLE_OFFER}
        }
    )


class GetOffersResponse(ListResponseSchema):
    data: List[OfferInDB] = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Offers found with success",
                "pagination": {"page": 1, "page_size": 2, "total": 2},
                "data": [
                    EXAMPLE_OFFER,
                    {**EXAMPLE_OFFER, "id": "off_456", "name": "Promo"},
                ],
            }
        }
    )


class CreateOfferResponse(Response):
    data: OfferInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"message": "Offer created with success", "data": EXAMPLE_OFFER}
        }
    )


class UpdateOfferResponse(Response):
    data: OfferInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"message": "Offer updated with success", "data": EXAMPLE_OFFER}
        }
    )


class DeleteOfferResponse(Response):
    data: OfferInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"message": "Offer deleted with success", "data": EXAMPLE_OFFER}
        }
    )
