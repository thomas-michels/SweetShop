from mongoengine import StringField, FloatField, ListField, EmbeddedDocument, EmbeddedDocumentListField, IntField, BooleanField
from app.core.models.base_document import BaseDocument


class Item(EmbeddedDocument):
    id = StringField(required=True)
    name = StringField(required=True)
    description = StringField(required=False)
    file_id = StringField(required=False)
    unit_price = FloatField(min_value=0, required=True)
    unit_cost = FloatField(min_value=0, required=True)


class Section(EmbeddedDocument):
    title = StringField(required=True)
    description = StringField(required=False)
    position = IntField(min_value=1, required=True)
    type = StringField(required=True)
    min_choices = IntField(min_value=0, required=True)
    max_choices = IntField(min_value=0, required=True)
    is_required = BooleanField(default=False)
    default_item_id = StringField(required=False)
    items = EmbeddedDocumentListField(Item, required=True)


class ProductModel(BaseDocument):
    organization_id = StringField(required=True)
    name = StringField(required=True)
    description = StringField(required=True)
    unit_price = FloatField(min_value=0, required=True)
    unit_cost = FloatField(min_value=0, required=True)
    tags = ListField(StringField(), required=False)
    file_id = StringField(required=False)
    sections = EmbeddedDocumentListField(Section, required=False)

    meta = {
        "collection": "products"
    }

    def update(self, **kwargs):
        self.base_update()
        kwargs.pop("updated_at")
        return super().update(updated_at=self.updated_at,**kwargs)

    def delete(self, soft_delete: bool = True, signal_kwargs=None, **write_concern):
        if soft_delete:
            self.soft_delete()
            self.save()

        else:
            return super().delete(signal_kwargs, **write_concern)
