from mongoengine import StringField, ListField, DictField, FloatField
from app.core.models.base_document import BaseDocument
from app.core.utils.utc_datetime import UTCDateTime


class PreOrderModel(BaseDocument):
    organization_id = StringField(required=True)
    user_id = StringField(required=True)
    code = StringField(required=True)
    menu_id = StringField(required=True)
    payment_method = StringField(required=True)
    customer = DictField(required=True)
    delivery = DictField(required=True)
    observation = StringField(required=False)
    total_amount = FloatField(required=False)
    total_cost = FloatField(required=False)
    status = StringField(default=None, required=False)
    items = ListField(DictField(), default=[])
    tax = FloatField(default=0, required=False)
    order_id = StringField(required=False)

    meta = {
        "collection": "pre_orders"
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
