from mongoengine import StringField, Document

from app.core.models.base_document import generate_prefixed_id


class MarketingEmailModel(Document):
    id = StringField(primary_key=True)
    name = StringField(required=True)
    email = StringField(required=True, unique=True)
    reason = StringField(required=True)
    description = StringField(required=False)

    meta = {
        "collection": "marketing_emails"
    }

    def save(self, *args, **kwargs):
        if not self.id:
            prefix = self.__class__.__name__.lower()[:3]
            self.id = generate_prefixed_id(prefix)

        super().save(*args, **kwargs)
