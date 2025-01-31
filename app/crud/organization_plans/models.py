from mongoengine import StringField, DateTimeField

from app.core.models.base_document import BaseDocument


class OrganizationPlanModel(BaseDocument):
    organization_id = StringField(required=True)
    plan_id = StringField(required=True)
    start_date = DateTimeField(required=True)
    end_date = DateTimeField(required=True)

    meta = {
        "collection": "organization_plans"
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
