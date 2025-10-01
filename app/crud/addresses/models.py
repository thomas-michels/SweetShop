from mongoengine import StringField, FloatField
from app.core.models.base_document import BaseDocument


class AddressModel(BaseDocument):
    zip_code = StringField(required=True, regex=r"^\d{5}-?\d{3}$")
    state = StringField(required=True)
    city = StringField(required=True)
    neighborhood = StringField(required=True)
    line_1 = StringField(required=True)
    line_2 = StringField(required=False)
    latitude = FloatField(required=False)
    longitude = FloatField(required=False)

    meta = {
        "collection": "addresses",
        "indexes": [
            {"fields": ["zip_code"], "unique": True}
        ]
    }

    def update(self, **kwargs):
        self.base_update()
        if kwargs.get("kwargs"):
            kwargs.pop("updated_at")
        return super().update(updated_at=self.updated_at, **kwargs)

    def delete(self, soft_delete: bool = True, signal_kwargs=None, **write_concern):
        if soft_delete:
            self.soft_delete()
            self.save()
        else:
            return super().delete(signal_kwargs, **write_concern)
