from mongoengine import StringField, FloatField, BooleanField

from app.core.models.base_document import BaseDocument
from app.core.utils.utc_datetime import UTCDateTime


class PlanFeatureModel(BaseDocument):
    plan_id = StringField(required=True)
    name = StringField(required=True)
    value = StringField(required=True)
    additional_price = FloatField(required=True)
    allow_additional = BooleanField(default=False)

    meta = {
        "collection": "plan_features"
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
