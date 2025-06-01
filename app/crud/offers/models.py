from mongoengine import StringField, BooleanField, ListField, DictField, FloatField, IntField

from app.core.models.base_document import BaseDocument
from app.core.utils.utc_datetime import UTCDateTime


class OfferModel(BaseDocument):
    organization_id = StringField(required=True)
    section_id = StringField(required=True)
    position = IntField(required=False)
    name = StringField(required=True)
    description = StringField(required=True)
    is_visible = BooleanField(default=True, required=False)
    unit_cost = FloatField(required=True)
    unit_price = FloatField(required=True)
    products = ListField(DictField(), min_lenght=1)

    meta = {
        "collection": "offers"
    }

    def update(self, **kwargs):
        self.base_update()
        kwargs.pop("updated_at")
        return super().update(updated_at=UTCDateTime.now(),**kwargs)

    def delete(self, soft_delete: bool = True, signal_kwargs=None, **write_concern):
        if soft_delete:
            self.soft_delete()
            self.save()

        else:
            return super().delete(signal_kwargs, **write_concern)
