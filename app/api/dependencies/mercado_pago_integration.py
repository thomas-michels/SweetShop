import mercadopago
from datetime import datetime, timedelta, timezone
from app.api.exceptions.authentication_exceptions import InternalErrorException
from app.api.shared_schemas.mercado_pago import MPSubscriptionModel
from app.core.configs import get_environment, get_logger
from app.core.exceptions.users import NotFoundError

_logger = get_logger(__name__)
_env = get_environment()


class MercadoPagoIntegration:
    def __init__(self):
        self.mp = mercadopago.SDK(_env.MERCADO_PAGO_ACCESS_TOKEN)

    def create_subscription(self, reason: str, price_monthly: float, user_info: dict, discount: float = 0) -> MPSubscriptionModel:
        """
        Cria uma assinatura anual no Mercado Pago.
        :param price_monthly: Preço mensal da assinatura.
        :param user_info: Informações do usuário (email, nome, etc.).
        """
        _logger.info(f"Calling create_subscription for user {user_info}")

        annual_price = round(((12 * price_monthly) - discount), 2)

        try:
            data = {
                "status": "pending",
                "auto_recurring": {
                    "frequency": 12,
                    "frequency_type": "months",
                    "transaction_amount": annual_price,
                    "currency_id": "BRL",
                    "start_date": (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat() + "Z",
                    "end_date": (datetime.now(timezone.utc) + timedelta(days=365)).isoformat() + "Z"
                },
                "payer_email": user_info["email"] if _env.ENVIRONMENT == "prod" else _env.MP_TEST_EMAIL,
                "back_url": f"{_env.PEDIDOZ_FRONT_URL}/",
                "reason": reason
            }

            response = self.mp.preapproval().create(data)

            _logger.info(f"Subscription created - {response['status']}")

            match response.get("status"):
                case 201:
                    return MPSubscriptionModel(**response["response"])

                case _:
                    _logger.error(f"Error on create subscription - Status: {response.get('status')} - Response: {response.get('response')}")
                    raise InternalErrorException("Error create subscription")

        except Exception as error:
            _logger.error(f"Error on create_subscription: {str(error)}")
            raise InternalErrorException("Error create subscription")

    def get_subscription(self, preapproval_id: str) -> MPSubscriptionModel:
        """
        Obtém os detalhes de uma assinatura.
        :param preapproval_id: ID da assinatura.
        """
        _logger.info(f"Calling get_subscription - preapproval_id: {preapproval_id}")
        try:
            response = self.mp.preapproval().get(preapproval_id)

            if response.get("status") == 200:
                return MPSubscriptionModel(**response["response"])

            elif response.get("status") == 404:
                _logger.warning(f"Subscription {preapproval_id} NOT found")
                raise NotFoundError(f"Subscription {preapproval_id} not found")

            else:
                _logger.error(f"Error fetching subscription - Status: {response.get('status')} - Response: {response.get('response')}")
                raise InternalErrorException(f"Error fetching subscription {preapproval_id}")

        except Exception as error:
            _logger.error(f"Error on get_subscription: {str(error)}")
            raise InternalErrorException(f"Error fetching subscription {preapproval_id}")

    def cancel_subscription(self, preapproval_id: str) -> MPSubscriptionModel:
        """
        Cancela uma assinatura ativa.
        :param preapproval_id: ID da assinatura no Mercado Pago.
        """
        _logger.info(f"Calling cancel_subscription - preapproval_id: {preapproval_id}")
        try:
            response = self.mp.preapproval().update(preapproval_id, {"status": "cancelled"})

            _logger.info("Subscription cancelled")
            if response.get("status") == 200:
                return MPSubscriptionModel(**response["response"])

            elif response.get("status") == 404:
                _logger.warning(f"Subscription {preapproval_id} NOT found")
                raise NotFoundError(f"Subscription {preapproval_id} not found")

            else:
                _logger.error(f"Error on cancel subscription - Status: {response.get('status')} - Response: {response.get('response')}")
                raise InternalErrorException(f"Error canceling subscription {preapproval_id}")

        except Exception as error:
            _logger.error(f"Error on cancel_subscription: {str(error)}")
            raise InternalErrorException(f"Error canceling subscription {preapproval_id}")

    def get_payment(self, payment_id: str) -> dict:
        """
        Obtém os detalhes de um pagamento no Mercado Pago.
        :param payment_id: ID do pagamento.
        """
        _logger.info(f"Calling get_payment - payment_id: {payment_id}")
        try:
            response = self.mp.payment().get(payment_id)

            if response.get("status") == 200:
                _logger.info(f"Payment {payment_id} found")
                return response["response"]

            elif response.get("status") == 404:
                _logger.warning(f"Payment {payment_id} NOT found")
                raise NotFoundError(f"PaymentId not found {payment_id}")

            else:
                _logger.error(f"Error on get payment - Status: {response.get('status')} - Response: {response.get('response')}")
                raise InternalErrorException("Error fetching payment details")

        except Exception as error:
            _logger.error(f"Error on get_payment: {str(error)}")
            raise InternalErrorException("Error fetching payment details")

    def get_authorized_payments(self, authorized_payment_id: str) -> dict:
        """
        Obtém os detalhes de um pagamento autorizado.
        :param authorized_payment_id: ID do pagamento autorizado.
        """
        _logger.info(f"Calling get_authorized_payments - authorized_payment_id: {authorized_payment_id}")
        try:
            response = self.mp.get(f"/v1/authorized_payments/{authorized_payment_id}")

            if response.get("status") == 200:
                _logger.info(f"Authorized payment {authorized_payment_id} found")
                return response["response"]

            elif response.get("status") == 404:
                _logger.warning(f"Authorized payment {authorized_payment_id} NOT found")
                raise NotFoundError(f"Authorized payment {authorized_payment_id} not found")

            else:
                _logger.error(f"Error on get authorized payment - Status: {response.get('status')} - Response: {response.get('response')}")
                raise InternalErrorException("Error fetching authorized payment details")

        except Exception as error:
            _logger.error(f"Error on get_authorized_payments: {str(error)}")
            raise InternalErrorException("Error fetching authorized payment details")
