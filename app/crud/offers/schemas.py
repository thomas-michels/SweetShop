from typing import List, Optional
from pydantic import Field
from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.core.utils.utc_datetime import UTCDateTime, UTCDateTimeType
from app.crud.files.schemas import FileInDB


class OfferProduct(GenericModel):
    product_id: str = Field(example="prod_123")
    name: str = Field(example="name")
    description: str = Field(example="description")
    unit_cost: float = Field(example=10)
    unit_price: float = Field(example=12)
    quantity: int = Field(default=1, example=1, ge=1)
    file_id: str | None = Field(default=None, example="file_123")


class CompleteOfferProduct(OfferProduct):
    file: FileInDB | None = Field(default=None)


class OfferProductRequest(GenericModel):
    product_id: str = Field(example="prod_123")
    quantity: int = Field(default=1, example=1, ge=1)


class RequestOffer(GenericModel):
    name: str = Field(example="Doces")
    description: str = Field(example="Bolos e tortas")
    products: List[OfferProductRequest] = Field(default=[], min_length=1)
    file_id: str | None = Field(default=None, example="file_123")
    unit_price: float | None = Field(default=None, example=12)
    starts_at: UTCDateTimeType | None = Field(default=None, example=str(UTCDateTime.now()))
    ends_at: UTCDateTimeType | None = Field(default=None, example=str(UTCDateTime.now()))
    is_visible: bool = Field(default=True)


class Offer(GenericModel):
    name: str = Field(example="Doces")
    description: str = Field(example="Bolos e tortas")
    products: List[OfferProduct] = Field(default=[])
    file_id: str | None = Field(default=None)
    unit_cost: float = Field(example=10)
    unit_price: float = Field(example=12)
    starts_at: UTCDateTimeType | None = Field(default=None, example=str(UTCDateTime.now()))
    ends_at: UTCDateTimeType | None = Field(default=None, example=str(UTCDateTime.now()))
    is_visible: bool = Field(default=True)

    def validate_updated_fields(self, update_offer: "UpdateOffer") -> bool:
        is_updated = False

        if update_offer.name is not None:
            self.name = update_offer.name
            is_updated = True

        if update_offer.description is not None:
            self.description = update_offer.description
            is_updated = True

        if update_offer.products is not None:
            is_updated = True

        if update_offer.file_id is not None:
            self.file_id = update_offer.file_id
            is_updated = True

        if update_offer.unit_price is not None:
            self.unit_price = update_offer.unit_price
            is_updated = True

        if update_offer.starts_at is not None:
            self.starts_at = update_offer.starts_at
            is_updated = True

        if update_offer.ends_at is not None:
            self.ends_at = update_offer.ends_at
            is_updated = True

        if update_offer.is_visible is not None:
            self.is_visible = update_offer.is_visible
            is_updated = True

        return is_updated


class UpdateOffer(GenericModel):
    name: Optional[str] = Field(default=None, example="Doces")
    description: Optional[str] = Field(default=None, example="Bolos e tortas")
    products: Optional[List[OfferProductRequest]] = Field(default=None, min_length=1)
    file_id: Optional[str] = Field(default=None)
    unit_price: Optional[float] = Field(default=None, example=12)
    starts_at: Optional[UTCDateTimeType] = Field(default=None, example=str(UTCDateTime.now()))
    ends_at: Optional[UTCDateTimeType] = Field(default=None, example=str(UTCDateTime.now()))
    is_visible: Optional[bool] = Field(default=None)


class OfferInDB(Offer, DatabaseModel):
    organization_id: str = Field(example="org_123")

class CompleteOffer(Offer, DatabaseModel):
    products: List[CompleteOfferProduct | str] = Field(default=[])
    file: FileInDB | None = Field(default=None)
