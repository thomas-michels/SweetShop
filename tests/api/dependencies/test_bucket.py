import time
import unittest
from unittest.mock import MagicMock, patch

from app.api.dependencies.bucket import S3BucketManager


class TestS3BucketManagerCaching(unittest.TestCase):
    @patch("app.api.dependencies.bucket.boto3.resource")
    @patch("app.api.dependencies.bucket.boto3.client")
    def test_generate_presigned_url_cached(self, mock_client, mock_resource):
        mock_client.return_value.generate_presigned_url.return_value = "signed1"
        mock_resource.return_value = MagicMock()
        S3BucketManager.set_cache({})
        manager = S3BucketManager(mode="private")
        manager.bucket_name = "bucket"

        url1 = manager.generate_presigned_url("http://example.com/bucket/file.txt", expiration=10)
        url2 = manager.generate_presigned_url("http://example.com/bucket/file.txt", expiration=10)

        self.assertEqual(url1, url2)
        mock_client.return_value.generate_presigned_url.assert_called_once()

    @patch("app.api.dependencies.bucket.boto3.resource")
    @patch("app.api.dependencies.bucket.boto3.client")
    def test_cache_expires_and_regenerates(self, mock_client, mock_resource):
        mock_client.return_value.generate_presigned_url.side_effect = ["url1", "url2"]
        mock_resource.return_value = MagicMock()
        S3BucketManager.set_cache({})
        manager = S3BucketManager(mode="private")
        manager.bucket_name = "bucket"

        url1 = manager.generate_presigned_url("http://example.com/bucket/file.txt", expiration=1)
        time.sleep(1.1)
        url2 = manager.generate_presigned_url("http://example.com/bucket/file.txt", expiration=1)

        self.assertEqual(url1, "url1")
        self.assertEqual(url2, "url2")
        self.assertEqual(mock_client.return_value.generate_presigned_url.call_count, 2)
