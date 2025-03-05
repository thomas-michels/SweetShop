from datetime import datetime
from mongoengine import StringField, FloatField, BooleanField, DateTimeField, IntField
from app.core.models.base_document import BaseDocument


class CouponModel(BaseDocument):
    name = StringField(max_length=30, required=True, unique=True)
    value = FloatField(required=True)
    is_percent = BooleanField(required=True)
    expires_at = DateTimeField(required=True)
    limit = IntField(required=True)
    usage_count = IntField(default=0, required=True)

    meta = {
        "collection": "coupons"
    }

    def update(self, **kwargs):
        self.base_update()
        if kwargs.get("updated_at"):
            kwargs.pop("updated_at")
            return super().update(updated_at=self.updated_at,**kwargs)

        return super().update(updated_at=datetime.now(), **kwargs)

    def delete(self, soft_delete: bool = True, signal_kwargs=None, **write_concern):
        if soft_delete:
            self.soft_delete()
            self.save()

        else:
            return super().delete(signal_kwargs, **write_concern)
