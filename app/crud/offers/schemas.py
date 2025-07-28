from typing import List, Optional
from pydantic import Field, model_validator
from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.crud.files.schemas import FileInDB


class OfferProduct(GenericModel):
    product_id: str = Field(example="prod_123")
    name: str = Field(example="name")
    description: str = Field(example="description")
    unit_cost: float = Field(example=10)
    unit_price: float = Field(example=12)
    file_id: str | None = Field(default=None, example="file_123")


class Additional(GenericModel):
    name: str = Field(example="Bacon")
    file_id: str | None = Field(default=None)
    unit_price: float = Field(ge=0)
    unit_cost: float = Field(ge=0)
    min_quantity: int = Field(default=1, ge=0)
    max_quantity: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def validate_quantities(self) -> "Additional":
        if self.max_quantity < self.min_quantity:
            raise ValueError("max_quantity must be greater than or equal to min_quantity")
        return self


class CompleteOfferProduct(OfferProduct):
    file: FileInDB | None = Field(default=None)


class RequestOffer(GenericModel):
    name: str = Field(example="Doces")
    description: str = Field(example="Bolos e tortas")
    products: List[str] = Field(default=[], min_length=1)
    additionals: List[Additional] = Field(default=[])


class Offer(GenericModel):
    name: str = Field(example="Doces")
    description: str = Field(example="Bolos e tortas")
    products: List[OfferProduct] = Field(default=[])
    additionals: List[Additional] = Field(default=[])
    unit_cost: float = Field(example=10)
    unit_price: float = Field(example=12)

    def validate_updated_fields(self, update_offer: "UpdateOffer") -> bool:
        is_updated = False

        if update_offer.name is not None:
            self.name = update_offer.name
            is_updated = True

        if update_offer.description is not None:
            self.description = update_offer.description
            is_updated = True

        if update_offer.products is not None:
            self.products = update_offer.products
            is_updated = True

        if update_offer.additionals is not None:
            self.additionals = update_offer.additionals
            is_updated = True

        return is_updated


class UpdateOffer(GenericModel):
    name: Optional[str] = Field(default=None, example="Doces")
    description: Optional[str] = Field(default=None, example="Bolos e tortas")
    products: Optional[List[str]] = Field(default=None, min_length=1)
    additionals: Optional[List[Additional]] = Field(default=None)


class OfferInDB(Offer, DatabaseModel):
    organization_id: str = Field(example="org_123")

class CompleteOffer(Offer, DatabaseModel):
    products: List[CompleteOfferProduct | str] = Field(default=[])
