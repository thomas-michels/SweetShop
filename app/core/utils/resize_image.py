from PIL import Image, ImageOps
from PIL.Image import Resampling
import io

from fastapi import UploadFile


async def resize_image(upload_image: UploadFile, size=(400, 400)) -> UploadFile:
    """Redimensiona a imagem para o tamanho especificado.

    Args:
        image (UploadFile): Imagem enviada pelo usuário.
        size (tuple, optional): Tamanho desejado (largura, altura). Default é (400, 400).

    Returns:
        UploadFile: Imagem redimensionada pronta para upload.
    """
    # Lê a imagem como um objeto de bytes
    upload_image.file.seek(0)
    img = Image.open(upload_image.file)

    img = ImageOps.exif_transpose(img)

    # Converte para RGB se necessário (evita problemas com transparência)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Redimensiona mantendo a proporção
    img.thumbnail(
        size=size,
        resample=Resampling.LANCZOS
    )

    # Salva a imagem redimensionada em um buffer de memória
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")  # Salvar como JPEG para otimizar espaço
    img_bytes.seek(0)

    # Retorna a imagem como um novo UploadFile
    new_name = f"{upload_image.filename.split('.')[0]}.jpeg"
    return UploadFile(filename=new_name, file=img_bytes, headers={"content_type": "image/jpeg"})
