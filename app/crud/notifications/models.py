from mongoengine import BooleanField, ListField, StringField

from app.core.models.base_document import BaseDocument
from app.core.utils.utc_datetime import UTCDateTime


class NotificationModel(BaseDocument):
    organization_id = StringField(required=True)
    user_id = StringField(required=True)
    title = StringField(required=True)
    content = StringField(required=True)
    channels = ListField(StringField(choices=("EMAIL", "APP")), default=list)
    read = BooleanField(default=False)
    notification_type = StringField(required=True)

    meta = {
        "collection": "notifications",
        "indexes": [
            "organization_id",
            "user_id",
            "notification_type",
        ],
    }

    def update(self, **kwargs):
        self.base_update()
        kwargs.pop("updated_at", None)
        return super().update(updated_at=UTCDateTime.now(), **kwargs)

    def delete(self, soft_delete: bool = True, signal_kwargs=None, **write_concern):
        if soft_delete:
            self.soft_delete()
            self.save()
        else:
            return super().delete(signal_kwargs, **write_concern)
