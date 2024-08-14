from datetime import datetime
from mongoengine import (
    BooleanField,
    DateTimeField
)


class BaseDocument:
    is_active: bool = BooleanField(default=True, required=True)
    created_at = DateTimeField(required=True)
    updated_at = DateTimeField(required=True)

    def base_update(self):
        self.updated_at = datetime.now()

    def soft_delete(self):
        self.is_active = False
        self.updated_at = datetime.now()
