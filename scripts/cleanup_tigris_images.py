from urllib.parse import urlparse

import boto3
from mongoengine import connect

from app.core.configs import get_environment
from app.crud.files.models import FileModel
from app.crud.files.schemas import FilePurpose


def get_s3_client():
    env = get_environment()
    return boto3.client(
        "s3",
        endpoint_url=env.BUCKET_BASE_URL,
        aws_access_key_id=env.BUCKET_ACCESS_KEY_ID,
        aws_secret_access_key=env.BUCKET_SECRET_KEY,
    )


def collect_referenced_files() -> set[str]:
    """Retorna o conjunto de chaves do bucket referenciadas na coleção 'files'."""
    purposes = [FilePurpose.PRODUCT.value, FilePurpose.OFFER.value]
    referenced: set[str] = set()

    for file in FileModel.objects(purpose__in=purposes):
        parsed = urlparse(file.url)
        referenced.add(parsed.path.lstrip("/"))

    return referenced


def main() -> None:
    """Lista e remove arquivos órfãos de imagens no bucket Tigris."""
    env = get_environment()
    connect(host=env.DATABASE_HOST)
    s3_client = get_s3_client()

    bucket_name = env.PRIVATE_BUCKET_NAME
    paginator = s3_client.get_paginator("list_objects_v2")
    stored_files = []
    for page in paginator.paginate(Bucket=bucket_name, Prefix="organization/"):
        for obj in page.get("Contents", []):
            stored_files.append(obj["Key"])

    referenced_files = collect_referenced_files()
    image_extensions = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")

    orphan_files = [
        key for key in stored_files
        if key.lower().endswith(image_extensions) and key not in referenced_files
    ]

    for key in orphan_files:
        s3_client.delete_object(Bucket=bucket_name, Key=key)
        print(f"Deleted: {key}")

    print(f"Total orphan files removed: {len(orphan_files)}")


if __name__ == "__main__":
    main()
