import boto3
import mimetypes
from boto3.s3.transfer import S3Transfer
from urllib.parse import urlparse
from app.core.configs import get_environment, get_logger

_env = get_environment()
_logger = get_logger(__name__)


class S3BucketManager:
    """
    Classe para gerenciamento de operações com o bucket S3.
    """

    def __init__(self, mode: str = "private"):
        self.client = boto3.client(
            "s3",
            endpoint_url=_env.BUCKET_BASE_URL,
            aws_access_key_id=_env.BUCKET_ACCESS_KEY_ID,
            aws_secret_access_key=_env.BUCKET_SECRET_KEY,
        )
        self.resource = boto3.resource(
            "s3",
            endpoint_url=_env.BUCKET_BASE_URL,
            aws_access_key_id=_env.BUCKET_ACCESS_KEY_ID,
            aws_secret_access_key=_env.BUCKET_SECRET_KEY,
        )

        if mode == "private":
            self.bucket_name = _env.PRIVATE_BUCKET_NAME

        else:
            self.bucket_name = _env.PUBLIC_BUCKET_NAME

    def upload_file(self, local_path: str, bucket_path: str) -> str:
        """
        Faz upload de um arquivo para o bucket S3.

        :param local_path: Caminho local do arquivo a ser enviado.
        :param bucket_path: Caminho no bucket onde o arquivo será armazenado.
        :return: URL pública do arquivo.
        """
        try:
            _logger.info(f"Uploading file to '{self.bucket_name}/{bucket_path}'...")

            content_type, _ = mimetypes.guess_type(local_path)
            if content_type is None:
                content_type = "application/octet-stream"

            transfer = S3Transfer(self.client)
            transfer.upload_file(
                local_path,
                self.bucket_name,
                bucket_path,
                extra_args={"ContentType": content_type}
            )

            file_url = f"{_env.BUCKET_BASE_URL}/{self.bucket_name}/{bucket_path}"

            _logger.info(f"File uploaded successfully: {file_url}")
            return file_url

        except Exception as error:
            _logger.error(f"Error uploading file: {error}")
            raise Exception("Error uploading file") from error

    def download_file(self, bucket_path: str, local_path: str) -> None:
        """
        Faz download de um arquivo do bucket S3.

        :param bucket_path: Caminho do arquivo no bucket.
        :param local_path: Caminho local onde o arquivo será salvo.
        """
        try:
            _logger.info(f"Downloading file from '{self.bucket_name}/{bucket_path}'...")
            self.client.download_file(self.bucket_name, bucket_path, local_path)
            _logger.info(f"File downloaded successfully to '{local_path}'.")

        except Exception as error:
            _logger.error(f"Error downloading file: {error}")
            raise Exception("Error downloading file") from error

    def generate_presigned_url(self, file_url: str, expiration: int = None) -> str:
        """
        Gera uma URL pré-assinada para acesso ao arquivo no bucket.

        :param file_url: Caminho do arquivo no bucket.
        :param expiration: Tempo de expiração da URL em segundos (padrão: configurado no ambiente).
        :return: URL pré-assinada.
        """
        expiration = expiration or _env.BUCKET_URL_EXPIRES_IN_SECONDS
        try:
            parsed_url = urlparse(file_url)
            bucket_path = parsed_url.path.removeprefix(f"/{self.bucket_name}/")

            if not bucket_path:
                raise ValueError("Invalid file URL. Could not extract the file path.")

            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": bucket_path},
                ExpiresIn=expiration,
            )
            return url

        except Exception as error:
            _logger.error(f"Error generating presigned URL: {error}")
            raise Exception("Error generating presigned URL") from error

    def list_files(self, prefix: str = "") -> list:
        """
        Lista arquivos no bucket com base em um prefixo.

        :param prefix: Prefixo opcional para filtrar os arquivos.
        :return: Lista de caminhos de arquivos.
        """
        try:
            _logger.info(f"Listing files in bucket '{self.bucket_name}' with prefix '{prefix}'...")
            bucket = self.resource.Bucket(self.bucket_name)
            files = [obj.key for obj in bucket.objects.filter(Prefix=prefix)]
            _logger.info(f"Files found: {len(files)}")
            return files

        except Exception as error:
            _logger.error(f"Error listing files: {error}")
            raise Exception("Error listing files") from error

    def delete_file(self, bucket_path: str) -> None:
        """
        Remove um arquivo do bucket S3.

        :param bucket_path: Caminho do arquivo no bucket.
        """
        try:
            _logger.info(f"Deleting file from '{self.bucket_name}/{bucket_path}'...")
            self.client.delete_object(Bucket=self.bucket_name, Key=bucket_path)
            _logger.info(f"File '{bucket_path}' deleted successfully.")

        except Exception as error:
            _logger.error(f"Error deleting file: {error}")
            raise Exception("Error deleting file") from error

    def delete_file_by_url(self, file_url: str) -> None:
        """
        Remove um arquivo do bucket S3 com base na URL.

        :param file_url: URL do arquivo no S3.
        """
        try:
            parsed_url = urlparse(file_url)
            bucket_path = parsed_url.path.removeprefix(f"/{self.bucket_name}/")

            if not bucket_path:
                raise ValueError("Invalid file URL. Could not extract the file path.")

            _logger.info(f"Deleting file from '{self.bucket_name}/{bucket_path}'...")
            self.client.delete_object(Bucket=self.bucket_name, Key=bucket_path)
            _logger.info(f"File '{bucket_path}' deleted successfully.")

        except Exception as error:
            _logger.error(f"Error deleting file: {error}")
            raise Exception("Error deleting file") from error
