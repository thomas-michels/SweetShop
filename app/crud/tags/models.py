from datetime import datetime
from mongoengine import StringField, DictField
from app.core.models.base_document import BaseDocument
from app.core.configs import get_logger

logger = get_logger(__name__)


class TagModel(BaseDocument):
    name = StringField(max_length=100, required=True)
    styling = DictField(required=False)
    organization_id = StringField(required=True)

    meta = {
        "collection": "tags"
    }

    def update(self, **kwargs):
        self.base_update()
        if kwargs.get("updated_at"):
            kwargs.pop("updated_at")
            return super().update(updated_at=self.updated_at,**kwargs)

        return super().update(updated_at=datetime.now(), **kwargs)

    def delete(self, soft_delete: bool = True, signal_kwargs=None, **write_concern):
        self._remove_tag_from_all_collections()

        if soft_delete:
            self.soft_delete()
            self.save()

        else:
            return super().delete(signal_kwargs, **write_concern)

    def _remove_tag_from_all_collections(self):
        """Remove a referência desta tag de todas as collections do banco."""
        tag_id = self.id
        db = self._get_db()

        collection_names = db.list_collection_names()

        for collection_name in collection_names:
            if collection_name == self._get_collection_name():
                continue

            result = db[collection_name].update_many(
                {"tags": tag_id},
                {"$pull": {"tags": tag_id}}
            )
            if result.modified_count > 0:
                logger.info(f"Tag {tag_id} removed from {result.modified_count} documents in {collection_name}")
