from mongoengine import (
    Document,
    StringField,
    BooleanField,
    DateTimeField
)


class UserModel(Document):
    first_name = StringField(max_length=50, required=True)
    last_name = StringField(max_length=100, required=True)
    email = StringField(max_length=100, unique=True, required=True, regex=r"^\S+@\S+\.\S+$")
    password = StringField(max_length=100, required=True)
    is_active: bool = BooleanField(default=True, required=True)
    created_at = DateTimeField(required=True)
    updated_at = DateTimeField(required=True)

    meta = {
        "collection": "users"
    }
