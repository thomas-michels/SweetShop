from mongoengine import StringField, BooleanField, IntField

from app.core.models.base_document import BaseDocument
from app.core.utils.utc_datetime import UTCDateTime



class SectionModel(BaseDocument):
    organization_id = StringField(required=True)
    menu_id = StringField(required=True)
    position = IntField(required=True)
    name = StringField(max_length=100, required=True)
    description = StringField(required=True)
    is_visible = BooleanField(default=True, required=False)

    meta = {
        "collection": "sections"
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
