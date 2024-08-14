from mongoengine import StringField, Document, FloatField

from app.core.models.base_document import BaseDocument



class ProductModel(Document, BaseDocument):
    name = StringField(max_length=100, required=True)
    unit_price = FloatField(min_value=0, required=True)
    unit_cost = FloatField(min_value=0, required=True)

    meta = {
        "collection": "products"
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
