from datetime import datetime

from mongoengine import (
    BooleanField,
    DateTimeField,
    DictField,
    FloatField,
    ListField,
    StringField,
)

from app.core.models.base_document import BaseDocument
from app.crud.orders.schemas import OrderStatus, PaymentStatus


class OrderModel(BaseDocument):
    organization_id = StringField(required=True)
    customer_id = StringField(required=False)
    status = StringField(
        required=True, choices=[status.value for status in OrderStatus]
    )
    payment_status = StringField(
        required=True, choices=[status.value for status in PaymentStatus]
    )
    products = ListField(DictField(), required=True, min_length=1)
    tags = ListField(StringField(), required=False)
    delivery = DictField(required=True)
    preparation_date = DateTimeField(required=True)
    total_amount = FloatField(required=True)
    additional = FloatField(default=0, required=False)
    discount = FloatField(default=0, required=False)
    description = StringField(required=False)
    reason_id = StringField(required=False)
    is_fast_order = BooleanField(required=False, default=False)
    payment_details = ListField(DictField(), required=False)

    meta = {"collection": "orders"}

    @staticmethod
    def get_payments():
        pipeline = [
            {
                '$lookup': {
                    'from': 'payments',
                    'localField': '_id',
                    'foreignField': 'order_id',
                    'as': 'payments'
                }
            }, {
                '$set': {
                    'id': '$_id',
                    'payments': {
                        '$map': {
                            'input': '$payments',
                            'as': 'payment',
                            'in': {
                                '$mergeObjects': [
                                    '$$payment', {
                                        'id': '$$payment._id'
                                    }
                                ]
                            }
                        }
                    }
                }
            }, {
                '$unset': [
                    '_id', 'payments._id'
                ]
            }
        ]

        return pipeline

    def update(self, **kwargs):
        self.base_update()
        if kwargs.get("updated_at"):
            kwargs.pop("updated_at")
            return super().update(updated_at=self.updated_at, **kwargs)

        return super().update(updated_at=datetime.now(), **kwargs)

    def delete(self, soft_delete: bool = True, signal_kwargs=None, **write_concern):
        if soft_delete:
            self.soft_delete()
            self.save()

        else:
            return super().delete(signal_kwargs, **write_concern)
