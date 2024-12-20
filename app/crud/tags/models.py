from datetime import datetime
from mongoengine import StringField, DictField, BooleanField, Document
from app.core.models.base_document import BaseDocument


class TagModel(Document, BaseDocument):
    name = StringField(max_length=100, required=True, unique=True)
    styling = DictField(required=False)
    organization_id = StringField(required=True)
    system_tag = BooleanField(default=False, required=True)

    meta = {
        "collection": "tags"
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
