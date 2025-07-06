from io import BytesIO
from fastapi import UploadFile, HTTPException
from PIL import Image, UnidentifiedImageError

MAX_FILE_SIZE_MB = 25
ALLOWED_IMAGE_FORMATS = {"jpeg", "png", "jpg"}


async def validate_image_file(image: UploadFile) -> str:
    """
    Valida se o arquivo é uma imagem válida, tem tamanho <= 25 MB
    e está em um dos formatos permitidos. Retorna o formato em lowercase.
    """
    # 1) Lê tudo do upload apenas uma vez
    contents = await image.read()

    # 2) Valida tamanho
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds {MAX_FILE_SIZE_MB} MB limit"
        )

    # 3) Verifica e extrai o formato via Pillow
    try:
        with Image.open(BytesIO(contents)) as img:
            img.verify()              # detecta corrupções
            fmt = img.format.lower()  # ex: "jpeg", "png"
    except (UnidentifiedImageError, Exception):
        raise HTTPException(status_code=400, detail="Invalid image format")

    # 4) Valida o formato
    if fmt not in ALLOWED_IMAGE_FORMATS:
        raise HTTPException(status_code=400, detail="Invalid image format")

    # 5) Reseta o ponteiro para usos futuros (save, process etc.)
    image.file.seek(0)

    return fmt
