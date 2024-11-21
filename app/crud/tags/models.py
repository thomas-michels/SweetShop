from mongoengine import StringField, DictField, BooleanField, Document


class TagModel(Document):
    name = StringField(max_length=100, required=True, unique=True)
    styling = DictField()
    organization_id = StringField(required=True)
    system_tag = BooleanField(default=False, required=True)

    meta = {
        "collection": "tags"
    }
