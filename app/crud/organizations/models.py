from mongoengine import DictField, ListField, StringField, FloatField

from app.core.models.base_document import BaseDocument
from app.core.utils.utc_datetime import UTCDateTime


class OrganizationModel(BaseDocument):
    name = StringField(required=True, unique=True)
    international_code = StringField(required=False)
    ddd = StringField(max_length=3, required=False)
    phone_number = StringField(max_length=9, required=False)
    email = StringField(required=False, default=None)
    address = DictField(required=False, default=None)
    document = StringField(required=False, default=None)
    language = StringField(required=False, default=None)
    currency = StringField(required=False, default=None)
    users = ListField(DictField())
    file_id = StringField(required=False, default=None)
    unit_distance = StringField(required=False, default=None)
    tax = FloatField(required=False, default=0)
    website = StringField(required=False, default=None)
    social_links = DictField(required=False, default=None)
    styling = DictField(required=False, default=None)

    meta = {"collection": "organizations"}

    def update(self, **kwargs):
        self.base_update()
        if kwargs.get("updated_at"):
            kwargs.pop("updated_at")
            return super().update(updated_at=self.updated_at, **kwargs)

        return super().update(updated_at=UTCDateTime.now(), **kwargs)

    def delete(self, soft_delete: bool = True, signal_kwargs=None, **write_concern):
        if soft_delete:
            self.soft_delete()
            self.save()

        else:
            return super().delete(signal_kwargs, **write_concern)
