from mongoengine import StringField, ListField, DictField, DateTimeField

from app.core.models.base_document import BaseDocument
from app.core.utils.utc_datetime import UTCDateTime


class CustomerModel(BaseDocument):
    organization_id = StringField(required=True)
    name = StringField(max_length=100, required=True)
    international_code = StringField(required=False, default=None)
    ddd = StringField(max_length=3, required=False)
    phone_number = StringField(max_length=9, required=False)
    document = StringField(required=False, default=None)
    email = StringField(required=False, default=None)
    addresses = ListField(DictField())
    tags = ListField(StringField(), required=False)
    date_of_birth = DateTimeField(required=False)

    meta = {
        "collection": "customers"
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
