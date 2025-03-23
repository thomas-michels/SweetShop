from enum import Enum
from pydantic import Field

from app.api.dependencies.bucket import S3BucketManager
from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel

class FilePurpose(str, Enum):
    PRODUCT = "PRODUCTS"
    ORGANIZATION = "ORGANIZATIONS"


class File(GenericModel):
    purpose: FilePurpose = Field(example=FilePurpose.PRODUCT)
    type: str = Field(example="txt")
    url: str = Field(example="www.tigris.com.br")


class FileInDB(File, DatabaseModel):
    organization_id: str = Field(example="org_123")

    def model_post_init(self, __context):
        s3_manager = S3BucketManager(mode="private")
        presigned_url = s3_manager.generate_presigned_url(
            file_url=self.url,
            expiration=600
        )
        self.url = presigned_url

        return super().model_post_init(__context)
