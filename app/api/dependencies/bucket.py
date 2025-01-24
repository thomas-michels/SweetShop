import boto3
from boto3.s3.transfer import S3Transfer
from app.core.configs import get_environment, get_logger

_env = get_environment()
_logger = get_logger(__name__)


class S3BucketManager:
    """
    Classe para gerenciamento de operações com o bucket S3.
    """

    def __init__(self):
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
        self.bucket_name = _env.BUCKET_NAME

    def upload_file(self, local_path: str, bucket_path: str) -> str:
        """
        Faz upload de um arquivo para o bucket S3.

        :param local_path: Caminho local do arquivo a ser enviado.
        :param bucket_path: Caminho no bucket onde o arquivo será armazenado.
        :return: URL pública do arquivo.
        """
        try:
            _logger.info(f"Uploading file to '{self.bucket_name}/{bucket_path}'...")
            transfer = S3Transfer(self.client)
            transfer.upload_file(local_path, self.bucket_name, bucket_path)
            file_url = f"{_env.BUCKET_BASE_URL}{self.bucket_name}/{bucket_path}"
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

    def generate_presigned_url(self, bucket_path: str, expiration: int = None) -> str:
        """
        Gera uma URL pré-assinada para acesso ao arquivo no bucket.

        :param bucket_path: Caminho do arquivo no bucket.
        :param expiration: Tempo de expiração da URL em segundos (padrão: configurado no ambiente).
        :return: URL pré-assinada.
        """
        expiration = expiration or _env.BUCKET_URL_EXPIRES_IN_SECONDS
        try:
            _logger.info(f"Generating presigned URL for '{bucket_path}'...")
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": bucket_path},
                ExpiresIn=expiration,
            )
            _logger.info(f"Presigned URL generated successfully.")
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
