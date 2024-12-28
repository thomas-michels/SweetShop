# from mongoengine import StringField, Document

# from app.core.models.base_document import BaseDocument



# class CustomerModel(BaseDocument):
#     name = StringField(max_length=100, required=True, unique=True)

#     meta = {
#         "collection": "customers"
#     }

#     def update(self, **kwargs):
#         self.base_update()
#         kwargs.pop("updated_at")
#         return super().update(updated_at=self.updated_at,**kwargs)

#     def delete(self, soft_delete: bool = True, signal_kwargs=None, **write_concern):
#         if soft_delete:
#             self.soft_delete()
#             self.save()

#         else:
#             return super().delete(signal_kwargs, **write_concern)
