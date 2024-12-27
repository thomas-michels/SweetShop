from datetime import datetime
from mongoengine import (
    Document,
    StringField,
    BooleanField,
    DateTimeField
)
from uuid import uuid4


def generate_prefixed_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


class BaseDocument(Document):
    meta = {'abstract': True}

    id = StringField(primary_key=True)
    is_active = BooleanField(default=True, required=True)
    created_at = DateTimeField(default=datetime.now, required=True)
    updated_at = DateTimeField(default=datetime.now, required=True)

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

    def soft_delete(self):
        self.is_active = False
        self.updated_at = datetime.now()
