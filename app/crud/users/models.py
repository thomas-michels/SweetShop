from mongoengine import StringField, Document

from app.core.models.base_document import BaseDocument


class UserModel(Document, BaseDocument):
    first_name = StringField(max_length=50, required=True)
    last_name = StringField(max_length=100, required=True)
    email = StringField(max_length=100, unique=True, required=True, regex=r"^\S+@\S+\.\S+$")
    password = StringField(max_length=100, required=True)

    meta = {
        "collection": "users"
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
