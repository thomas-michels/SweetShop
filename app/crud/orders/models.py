from datetime import datetime
from mongoengine import (
    Document,
    StringField,
    ListField,
    FloatField,
    BooleanField,
    DictField,
    DateTimeField
)
from app.core.models.base_document import BaseDocument
from app.crud.orders.schemas import OrderStatus, PaymentStatus


class OrderModel(Document, BaseDocument):
    organization_id = StringField(required=True)
    customer_id = StringField(required=False)
    status = StringField(required=True, choices=[status.value for status in OrderStatus])
    payment_status = StringField(required=True, choices=[status.value for status in PaymentStatus])
    products = ListField(DictField(), required=True, min_length=1)
    tags = ListField(StringField(), required=False)
    delivery = DictField(required=True)
    preparation_date = DateTimeField(required=True)
    additional = FloatField(default=0, required=False)
    value = FloatField(required=True)
    description = StringField(required=False)
    reason_id = StringField(required=False)
    is_active = BooleanField(required=True, default=True)

    meta = {
        "collection": "orders"
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
