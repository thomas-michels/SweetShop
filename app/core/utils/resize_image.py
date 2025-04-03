from PIL import Image, ImageOps
import io

from fastapi import UploadFile


async def resize_image(upload_image: UploadFile, size=(400, 400)):
    # Lê a imagem
    upload_image.file.seek(0)
    img = Image.open(upload_image.file)

    # Corrige a orientação (se necessário)
    img = ImageOps.exif_transpose(img)

    # Converte para RGB (se necessário)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Calcula o novo tamanho mantendo a proporção
    original_width, original_height = img.size
    target_width, target_height = size
    ratio = min(target_width / original_width, target_height / original_height)
    new_width = int(original_width * ratio)
    new_height = int(original_height * ratio)

    # Redimensiona a imagem
    img = img.resize((new_width, new_height), resample=Image.Resampling.LANCZOS)

    # Adiciona bordas para atingir o tamanho exato
    img = ImageOps.pad(
        img,
        size=size,  # Tamanho final desejado (ex.: 400x400)
        method=Image.Resampling.LANCZOS,
        color="white",  # Cor das bordas
        centering=(0.5, 0.5)  # Centraliza a imagem
    )

    # Salva em um buffer de memória
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    # Retorna como UploadFile
    new_name = f"{upload_image.filename.split('.')[0]}.jpeg"
    return UploadFile(filename=new_name, file=img_bytes, headers={"content_type": "image/jpeg"})
