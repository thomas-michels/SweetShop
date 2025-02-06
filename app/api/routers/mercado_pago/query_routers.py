from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Query, Request, Security, Response

router = APIRouter(prefix="/mercado-pago", tags=["Mercado Pago"])


@router.post("/webhook")
async def webhook(request: Request):
    """
    Webhook para capturar notificações de pagamento do Mercado Pago.
    """
    data = await request.json()
    print("Notificação recebida:", data)

    # Aqui você pode processar a notificação e atualizar o status da assinatura no banco de dados

    return {"status": "received"}
