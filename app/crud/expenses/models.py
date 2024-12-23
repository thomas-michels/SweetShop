from mongoengine import StringField, Document, DateField, FloatField, ListField, DictField

from app.core.models.base_document import BaseDocument


class ExpenseModel(Document, BaseDocument):
    organization_id = StringField(required=True)
    name = StringField(max_length=120, required=True)
    expense_date = DateField(required=True)
    total_paid = FloatField(required=True)
    payment_details = ListField(DictField(), required=False)

    meta = {
        "collection": "expenses"
    }

    def update(self, **kwargs):
        self.base_update()
        kwargs.pop("updated_at")
        return super().update(updated_at=self.updated_at,**kwargs)

    def delete(self, soft_delete: bool = True, signal_kwargs=None, **write_concern):
        if soft_delete:
            self.soft_delete()
            self.save()

        else:
            return super().delete(signal_kwargs, **write_concern)
