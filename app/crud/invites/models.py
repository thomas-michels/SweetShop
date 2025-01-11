from datetime import datetime
from mongoengine import StringField, BooleanField, DateTimeField, Document

from app.core.models.base_document import generate_prefixed_id


class InviteModel(Document):
    id = StringField(primary_key=True)
    user_email = StringField(required=True, unique_with="organization_id")
    role = StringField(required=True)
    organization_id = StringField(required=True)
    is_accepted = BooleanField(default=False, required=True)
    expires_at = DateTimeField(required=False)
    created_at = DateTimeField(default=datetime.now, required=True)
    updated_at = DateTimeField(default=datetime.now, required=True)

    meta = {
        "collection": "invites"
    }

    def save(self, *args, **kwargs):
        if not self.id:
            prefix = self.__class__.__name__.lower()[:3]
            self.id = generate_prefixed_id(prefix)

        if not self.created_at:
            self.created_at = datetime.now()

        self.updated_at = datetime.now()
        super().save(*args, **kwargs)

    def base_update(self):
        self.updated_at = datetime.now()

    def update(self, **kwargs):
        self.base_update()
        if kwargs.get("updated_at"):
            kwargs.pop("updated_at")
            return super().update(updated_at=self.updated_at,**kwargs)

        return super().update(updated_at=datetime.now(), **kwargs)
