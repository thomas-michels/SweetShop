import unittest
from enum import Enum
from types import SimpleNamespace

from app.crud.section_items.schemas import SectionItemInDB, ItemType, CompleteSectionItem
from app.core.utils.utc_datetime import UTCDateTime


class OptionKind(str, Enum):
    RADIO = "RADIO"
    CHECKBOX = "CHECKBOX"
    NUMBER = "NUMBER"


class TestSectionProductAdditionals(unittest.TestCase):
    def _section_item(self):
        return SectionItemInDB(
            id="rel",
            organization_id="org1",
            section_id="sec",
            item_id="prod",
            item_type=ItemType.PRODUCT,
            position=1,
            is_visible=True,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
            is_active=True,
        )

    def test_product_additional_option_types(self):
        for option in OptionKind:
            additional = SimpleNamespace(selection_type=option)
            product = SimpleNamespace(additionals=[additional])
            section_item = self._section_item()
            complete = CompleteSectionItem.model_validate(section_item)
            complete.product = product
            self.assertEqual(
                complete.product.additionals[0].selection_type, option
            )
