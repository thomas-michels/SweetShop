from mongoengine import StringField, FloatField, IntField

from app.core.models.base_document import BaseDocument
from app.core.utils.utc_datetime import UTCDateTime


class AdditionalItemModel(BaseDocument):
    organization_id = StringField(required=True)
    additional_id = StringField(required=True)
    position = IntField(required=True)
    product_id = StringField(required=False)
    file_id = StringField(required=False, default=None)
    label = StringField(required=True)
    unit_price = FloatField(required=True)
    unit_cost = FloatField(required=True)
    consumption_factor = FloatField(required=True)

    meta = {"collection": "additional_items"}

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
