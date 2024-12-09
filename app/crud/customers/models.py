from mongoengine import StringField, Document, ListField, DictField

from app.core.models.base_document import BaseDocument


class CustomerModel(Document, BaseDocument):
    organization_id = StringField(required=True)
    name = StringField(max_length=100, required=True)
    ddd = StringField(max_length=3, required=False)
    phone_number = StringField(max_length=9, required=False)
    addresses = ListField(DictField())
    tags = ListField(StringField(), required=False)

    meta = {
        "collection": "customers"
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
