from mongoengine import StringField, FloatField, DateTimeField, DictField

from app.core.models.base_document import BaseDocument
from app.core.utils.utc_datetime import UTCDateTime


class InvoiceModel(BaseDocument):
    organization_plan_id = StringField(required=True)
    integration_id = StringField(required=True)
    integration_type = StringField(required=True)
    amount = FloatField(required=True)
    amount_paid = FloatField(required=False)
    paid_at = DateTimeField(required=False)
    status = StringField(required=True)
    observation = DictField(dafault={})

    meta = {
        "collection": "invoices"
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
