from mongoengine import StringField, FloatField, ListField
from app.core.models.base_document import BaseDocument
from app.core.utils.utc_datetime import UTCDateTime


class ProductModel(BaseDocument):
    organization_id = StringField(required=True)
    name = StringField(required=True)
    description = StringField(required=True)
    unit_price = FloatField(min_value=0, required=True)
    unit_cost = FloatField(min_value=0, required=True)
    kind = StringField(default="REGULAR")
    tags = ListField(StringField(), required=False)
    file_id = StringField(required=False)

    meta = {
        "collection": "products"
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
