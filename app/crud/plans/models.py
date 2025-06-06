from mongoengine import StringField, FloatField

from app.core.models.base_document import BaseDocument
from app.core.utils.utc_datetime import UTCDateTime


class PlanModel(BaseDocument):
    name = StringField(required=True)
    description = StringField(required=True)
    price = FloatField(required=True)
    hide = FloatField(default=False, required=False)

    meta = {
        "collection": "plans"
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
