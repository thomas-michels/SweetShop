from mongoengine import StringField, BooleanField, DictField, ListField, IntField, FloatField

from app.core.models.base_document import BaseDocument


class MenuModel(BaseDocument):
    organization_id = StringField(required=True)
    name = StringField(required=True)
    description = StringField(required=True)
    is_visible = BooleanField(default=True, required=False)
    operating_days = ListField(DictField(), required=False)
    min_delivery_time = IntField(required=False)
    max_delivery_time = IntField(required=False)
    max_distance: int = IntField(required=False)
    allowed_payment_methods = ListField(StringField(), required=False)
    min_order_price = FloatField(required=False)
    min_delivery_price = FloatField(required=False)
    max_delivery_price = FloatField(required=False)
    km_tax = FloatField(required=False) # TODO remove that soon
    unit_tax = FloatField(required=False)
    accept_delivery: bool = BooleanField(default=True, required=False)

    meta = {
        "collection": "menus"
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
