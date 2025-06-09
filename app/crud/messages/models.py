from mongoengine import StringField
from app.core.models.base_document import BaseDocument
from app.core.utils.utc_datetime import UTCDateTime


class MessageModel(BaseDocument):
    international_code = StringField(required=True)
    ddd = StringField(required=True)
    phone_number = StringField(required=True)
    origin = StringField(required=True)
    message = StringField(required=True)
    message_type = StringField(required=True)
    organization_id = StringField(required=True)
    integration_id = StringField(required=True)

    meta = {
        "collection": "messages"
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
