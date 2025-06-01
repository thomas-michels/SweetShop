from mongoengine import DateTimeField, FloatField, StringField
from app.core.models.base_document import BaseDocument
from app.core.utils.utc_datetime import UTCDateTime


class PaymentModel(BaseDocument):
    order_id = StringField(required=True, index=True)
    organization_id = StringField(required=True)
    method = StringField(required=True)
    payment_date = DateTimeField(required=True)
    amount = FloatField(default=0, required=True)

    meta = {"collection": "payments", "indexes": [{"fields": ["order_id"]}]}

    def update(self, **kwargs):
        self.base_update()
        if kwargs.get("updated_at"):
            kwargs.pop("updated_at")
            return super().update(updated_at=self.updated_at, **kwargs)

        return super().update(updated_at=UTCDateTime.now(), **kwargs)

    def delete(self):
        self.soft_delete()
        self.save()
