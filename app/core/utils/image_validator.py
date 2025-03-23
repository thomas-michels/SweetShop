import imghdr
from fastapi import UploadFile, HTTPException

MAX_FILE_SIZE_MB = 25
ALLOWED_IMAGE_FORMATS = {"jpeg", "png", "jpg"}


async def validate_image_file(image: UploadFile) -> str:
    """Valida se o arquivo é uma imagem válida e tem no máximo 25MB.

    Args:
        image (UploadFile): Arquivo de imagem enviado.

    Returns:
        str: Tipo da imagem (jpeg, png, etc.).

    Raises:
        HTTPException: Se o arquivo não for uma imagem válida ou exceder o tamanho máximo.
    """
    # Verifica tamanho do arquivo

    image.file.seek(0, 2)  # Move o cursor para o final do arquivo

    file_size_mb = image.file.tell() / (1024 * 1024)

    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit")

    image.file.seek(0)  # Retorna o cursor para o início

    # Verifica se é uma imagem válida
    image_type = imghdr.what(image.file)
    if image_type not in ALLOWED_IMAGE_FORMATS:
        raise HTTPException(status_code=400, detail="Invalid image format")

    return image_type
