from enum import Enum
from typing import Optional
from pydantic import Field
from typing import Any

try:  # pragma: no cover - optional import for type checking
    from app.crud.offers.schemas import CompleteOffer  # type: ignore
    from app.crud.products.schemas import CompleteProduct  # type: ignore
except Exception:  # pragma: no cover
    CompleteOffer = CompleteProduct = Any

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel


class ItemType(str, Enum):
    OFFER = "OFFER"
    PRODUCT = "PRODUCT"


class SectionItem(GenericModel):
    section_id: str = Field(example="sec_123")
    item_id: str = Field(example="item_123")
    item_type: ItemType = Field(example=ItemType.OFFER)
    position: int = Field(example=1)
    is_visible: bool = Field(default=True, example=True)

    def validate_updated_fields(self, update_section_item: "UpdateSectionItem") -> bool:
        is_updated = False

        if update_section_item.position is not None:
            self.position = update_section_item.position
            is_updated = True

        if update_section_item.is_visible is not None:
            self.is_visible = update_section_item.is_visible
            is_updated = True

        return is_updated


class UpdateSectionItem(GenericModel):
    position: Optional[int] = Field(default=None, example=1)
    is_visible: Optional[bool] = Field(default=None, example=True)


class SectionItemInDB(SectionItem, DatabaseModel):
    organization_id: str = Field(example="org_123")


class CompleteSectionItem(SectionItemInDB):
    offer: "CompleteOffer | None" = Field(default=None)
    product: "CompleteProduct | None" = Field(default=None)


CompleteSectionItem.model_rebuild()
