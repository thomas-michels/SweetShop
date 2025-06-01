from mongoengine import StringField, DateTimeField, FloatField, ListField, DictField

from app.core.models.base_document import BaseDocument
from app.core.utils.utc_datetime import UTCDateTime


class ExpenseModel(BaseDocument):
    organization_id = StringField(required=True)
    name = StringField(max_length=120, required=True)
    expense_date = DateTimeField(required=True)
    total_paid = FloatField(required=True)
    payment_details = ListField(DictField(), required=False)
    tags = ListField(StringField(), required=False)

    meta = {
        "collection": "expenses"
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
