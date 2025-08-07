from mongoengine import StringField, IntField, BooleanField

from app.core.models.base_document import BaseDocument
from app.core.utils.utc_datetime import UTCDateTime


class SectionOfferModel(BaseDocument):
    organization_id = StringField(required=True)
    section_id = StringField(required=True)
    offer_id = StringField(required=False)
    product_id = StringField(required=False)
    position = IntField(required=True)
    is_visible = BooleanField(default=True)

    meta = {
        "collection": "section_offers"
    }

    def update(self, **kwargs):
        self.base_update()
        kwargs.pop("updated_at")
        return super().update(updated_at=UTCDateTime.now(), **kwargs)

    def delete(self, soft_delete: bool = True, signal_kwargs=None, **write_concern):
        if soft_delete:
            self.soft_delete()
            self.save()
        else:
            return super().delete(signal_kwargs, **write_concern)
