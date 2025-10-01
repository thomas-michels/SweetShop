from mongoengine import DateTimeField, StringField

from app.core.models.base_document import BaseDocument
from app.core.utils.utc_datetime import UTCDateTime


class BusinessDayModel(BaseDocument):
    organization_id = StringField(required=True)
    menu_id = StringField(required=True)
    day = StringField(required=True)
    closes_at = DateTimeField(required=True)

    meta = {
        "collection": "business_days",
        "indexes": [
            {
                "fields": ["organization_id", "menu_id", "day"],
                "unique": True,
            },
        ],
    }

    def update(self, **kwargs):
        self.base_update()
        kwargs.pop("updated_at", None)
        return super().update(updated_at=UTCDateTime.now(), **kwargs)
