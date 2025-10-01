from mongoengine import StringField, IntField

from app.core.models.base_document import BaseDocument
from app.core.utils.utc_datetime import UTCDateTime


class ProductAdditionalModel(BaseDocument):
    organization_id = StringField(required=True)
    product_id = StringField(required=True)
    name = StringField(required=True)
    selection_type = StringField(required=True)
    min_quantity = IntField(required=True)
    max_quantity = IntField(required=True)
    position = IntField(required=True)

    meta = {
        "collection": "product_additionals"
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
