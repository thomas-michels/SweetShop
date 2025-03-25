from mongoengine import StringField, BooleanField, DictField

from app.core.models.base_document import BaseDocument


class MenuModel(BaseDocument):
    organization_id = StringField(required=True)
    name = StringField(required=True)
    description = StringField(required=True)
    is_visible = BooleanField(default=True, required=False)
    extra_fields = DictField(default={}, required=False)

    meta = {
        "collection": "menus"
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
