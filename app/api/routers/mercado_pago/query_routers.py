from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Query, Request, Security, Response

router = APIRouter(prefix="/mercado-pago", tags=["Mercado Pago"])


# @router.post("/webhook")
# async def webhook(request: Request):
#     """
#     Webhook para capturar notificações de pagamento do Mercado Pago.
#     """
#     data = await request.json()
#     print("Notificação recebida:", data)

#     # Aqui você pode processar a notificação e atualizar o status da assinatura no banco de dados

#     return {"status": "received"}


# @router.post("/subscription")
# async def create_subscription(preapproval_plan_id: str, user_info: dict):
#     mercado_pago = MercadoPagoSubscription(access_token="SEU_ACCESS_TOKEN")
#     response = mercado_pago.create_subscription(preapproval_plan_id, user_info)
#     return response


# @router.get("/subscription/{}")
# async def create_subscription(preapproval_plan_id: str, user_info: dict):
#     mercado_pago = MercadoPagoSubscription(access_token="SEU_ACCESS_TOKEN")
#     response = mercado_pago.create_subscription(preapproval_plan_id, user_info)
#     return response


# @router.post("/webhook")
# async def webhook(request: Request):
#     data = await request.json()
#     print("Notificação recebida:", data)
#     return {"status": "received"}
