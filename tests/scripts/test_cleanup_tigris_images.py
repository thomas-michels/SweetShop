from types import SimpleNamespace

import pytest

from scripts import cleanup_tigris_images


def test_collect_referenced_files(monkeypatch):
    class FakeFile:
        def __init__(self, url):
            self.url = url

    fake_files = [
        FakeFile("https://cdn.local/organization/file1.png"),
        FakeFile("https://cdn.local/organization/file2.jpg"),
    ]

    monkeypatch.setattr(
        cleanup_tigris_images,
        "FileModel",
        SimpleNamespace(objects=lambda **kwargs: fake_files),
    )

    referenced = cleanup_tigris_images.collect_referenced_files()

    assert referenced == {
        "organization/file1.png",
        "organization/file2.jpg",
    }


def test_main_deletes_orphan_files(monkeypatch, capsys):
    class FakePaginator:
        def paginate(self, Bucket, Prefix):
            assert Bucket == "bucket"
            assert Prefix == "organization/"
            yield {
                "Contents": [
                    {"Key": "organization/file1.png"},
                    {"Key": "organization/file2.jpg"},
                    {"Key": "organization/file3.txt"},
                ]
            }

    class FakeS3Client:
        def __init__(self):
            self.deleted = []

        def get_paginator(self, name):
            assert name == "list_objects_v2"
            return FakePaginator()

        def delete_object(self, Bucket, Key):
            self.deleted.append((Bucket, Key))

    fake_client = FakeS3Client()

    monkeypatch.setattr(cleanup_tigris_images, "get_s3_client", lambda: fake_client)
    monkeypatch.setattr(
        cleanup_tigris_images,
        "collect_referenced_files",
        lambda: {"organization/file1.png"},
    )
    monkeypatch.setattr(
        cleanup_tigris_images,
        "get_environment",
        lambda: SimpleNamespace(
            BUCKET_BASE_URL="http://bucket",
            BUCKET_ACCESS_KEY_ID="id",
            BUCKET_SECRET_KEY="secret",
            PRIVATE_BUCKET_NAME="bucket",
            DATABASE_HOST="mongodb://localhost/test",
        ),
    )
    monkeypatch.setattr(cleanup_tigris_images, "connect", lambda host: None)

    cleanup_tigris_images.main()

    assert fake_client.deleted == [("bucket", "organization/file2.jpg")]
    captured = capsys.readouterr()
    assert "Deleted: organization/file2.jpg" in captured.out
    assert "Total orphan files removed: 1" in captured.out
