import mercadopago
from datetime import datetime, timedelta, timezone
from app.api.shared_schemas.mercado_pago import MPSubscriptionModel
from app.core.configs import get_environment, get_logger

_logger = get_logger(__name__)
_env = get_environment()


class MercadoPagoIntegration:
    def __init__(self):
        self.mp = mercadopago.SDK(_env.MERCADO_PAGO_ACCESS_TOKEN)

    def create_subscription(self, reason: str, price_monthly: float, user_info: dict) -> MPSubscriptionModel:
        """
        Cria uma assinatura anual no Mercado Pago.
        :param price_monthly: Preço mensal da assinatura.
        :param user_info: Informações do usuário (email, nome, etc.).
        """
        _logger.info(f"Calling create_subscription for user {user_info}")

        data = {
            "status": "pending",
            "auto_recurring": {
                "frequency": 12,
                "frequency_type": "months",
                "transaction_amount": price_monthly,
                "currency_id": "BRL",
                "start_date": (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat() + "Z",
                "end_date": (datetime.now(timezone.utc) + timedelta(days=365)).isoformat() + "Z"
            },
            "payer_email": user_info["email"],
            "back_url": user_info.get("back_url", f"{_env.PEDIDOZ_FRONT_URL}/"), # TODO change to the thank you route soon
            "reason": reason
        }

        response = self.mp.preapproval().create(data)

        _logger.info(f"Subscription created - {response['status']}")

        match response.get("status"):
            case 201:
                return MPSubscriptionModel(**response["response"])

            case _:
                raise Exception("Error on create subscription")

    def get_subscription(self, preapproval_id: str) -> MPSubscriptionModel:
        """
        Obtém os detalhes de uma assinatura.
        :param preapproval_id: ID da assinatura.
        """
        _logger.info(f"Calling get_subscription - preapproval_id: {preapproval_id}")

        response = self.mp.preapproval().get(preapproval_id)

        return MPSubscriptionModel(**response)

    def cancel_subscription(self, preapproval_id: str) -> MPSubscriptionModel:
        """
        Cancela uma assinatura ativa.
        :param preapproval_id: ID da assinatura no Mercado Pago.
        """
        _logger.info(f"Calling cancel_subscription - preapproval_id: {preapproval_id}")

        response = self.mp.preapproval().update(preapproval_id, {"status": "cancelled"})

        _logger.info("Subscription cancelled")
        return MPSubscriptionModel(**response)
