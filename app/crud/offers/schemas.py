from typing import List, Optional
from pydantic import Field
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


class CompleteOfferProduct(OfferProduct):
    file: FileInDB | None = Field(default=None)


class RequestOffer(GenericModel):
    section_id: str = Field(example="men_123")
    position: int | None = Field(default=1, example=1)
    name: str = Field(example="Doces")
    description: str = Field(example="Bolos e tortas")
    is_visible: bool = Field(default=False, example=True)
    products: List[str] = Field(default=[], min_length=1)


class Offer(GenericModel):
    section_id: str = Field(example="men_123")
    position: int | None = Field(default=1, example=1)
    name: str = Field(example="Doces")
    description: str = Field(example="Bolos e tortas")
    is_visible: bool = Field(default=False, example=True)
    products: List[OfferProduct] = Field(default=[])
    unit_cost: float = Field(example=10)
    unit_price: float = Field(example=12)

    def validate_updated_fields(self, update_offer: "UpdateOffer") -> bool:
        is_updated = False

        if update_offer.position is not None:
            self.position = update_offer.position
            is_updated = True

        if update_offer.name is not None:
            self.name = update_offer.name
            is_updated = True

        if update_offer.description is not None:
            self.description = update_offer.description
            is_updated = True

        if update_offer.is_visible is not None:
            self.is_visible = update_offer.is_visible
            is_updated = True

        if update_offer.products is not None:
            self.products = update_offer.products
            is_updated = True

        return is_updated


class UpdateOffer(GenericModel):
    position: Optional[int] = Field(default=None, example=1)
    name: Optional[str] = Field(default=None, example="Doces")
    description: Optional[str] = Field(default=None, example="Bolos e tortas")
    is_visible: Optional[bool] = Field(default=None, example=True)
    products: Optional[List[str]] = Field(default=None, min_length=1)


class OfferInDB(Offer, DatabaseModel):
    organization_id: str = Field(example="org_123")

class CompleteOffer(Offer, DatabaseModel):
    products: List[CompleteOfferProduct | str] = Field(default=[])
