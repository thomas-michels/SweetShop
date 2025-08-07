from typing import Optional

from app.crud.offers.schemas import OfferInDB
from app.crud.products.schemas import ProductInDB

from pydantic import Field

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel


class SectionOffer(GenericModel):
    section_id: str = Field(example="sec_123")
    offer_id: Optional[str] = Field(default=None, example="off_123")
    product_id: Optional[str] = Field(default=None, example="prod_123")
    position: int = Field(example=1)
    is_visible: bool = Field(default=True, example=True)

    def validate_updated_fields(self, update_section_offer: "UpdateSectionOffer") -> bool:
        is_updated = False

        if update_section_offer.position is not None:
            self.position = update_section_offer.position
            is_updated = True

        if update_section_offer.is_visible is not None:
            self.is_visible = update_section_offer.is_visible
            is_updated = True

        return is_updated


class UpdateSectionOffer(GenericModel):
    position: Optional[int] = Field(default=None, example=1)
    is_visible: Optional[bool] = Field(default=None, example=True)


class SectionOfferInDB(SectionOffer, DatabaseModel):
    organization_id: str = Field(example="org_123")


class CompleteSectionOffer(SectionOfferInDB):
    offer: OfferInDB | None = Field(default=None)
    product: ProductInDB | None = Field(default=None)
