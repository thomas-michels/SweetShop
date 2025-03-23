from datetime import datetime
from mongoengine import (
    StringField,
    DictField,
    ListField,
)
from app.core.models.base_document import BaseDocument


class OrganizationModel(BaseDocument):
    name = StringField(required=True, unique=True)
    ddd = StringField(max_length=3, required=False)
    phone_number = StringField(max_length=9, required=False)
    email = StringField(required=False, default=None)
    address = DictField(required=False, default=None)
    document = StringField(required=False, default=None)
    users = ListField(DictField())
    file_id = StringField(required=False, default=None)

    meta = {
        "collection": "organizations"
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
