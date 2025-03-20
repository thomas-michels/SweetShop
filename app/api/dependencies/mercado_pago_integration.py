import mercadopago
from datetime import datetime, timedelta, timezone
from app.api.exceptions.authentication_exceptions import InternalErrorException
from app.api.shared_schemas.mercado_pago import MPPreferenceModel, MPSubscriptionModel
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

    def create_preference(self, reason: str, price_monthly: float, user_info: dict, discount: float = 0) -> MPPreferenceModel:
        """
        Cria uma preferência de pagamento avulso no Mercado Pago.
        :param reason: Descrição do pagamento.
        :param amount: Valor total do pagamento.
        :param user_info: Informações do usuário (email, nome, etc.).
        """
        _logger.info(f"Calling create_preference for user {user_info}")

        try:
            data = {
                "items": [
                    {
                        "title": reason,
                        "quantity": 1,
                        "unit_price": round(price_monthly - discount, 2),
                        "currency_id": "BRL"
                    }
                ],
                "payer": {
                    # "email": user_info["email"] if _env.ENVIRONMENT == "prod" else _env.MP_TEST_EMAIL,
                },
                "back_urls": {
                    "success": f"{_env.PEDIDOZ_FRONT_URL}/",
                    "failure": f"{_env.PEDIDOZ_FRONT_URL}/",
                    "pending": f"{_env.PEDIDOZ_FRONT_URL}/"
                },
                "auto_return": "approved",
                "external_reference": f"pref_{user_info.get('id', 'no_id')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }

            response = self.mp.preference().create(data)

            _logger.info(f"Preference created - {response['status']}")

            match response.get("status"):
                case 201:
                    return MPPreferenceModel(**response["response"])

                case _:
                    _logger.error(f"Error on create preference - Status: {response.get('status')} - Response: {response.get('response')}")
                    raise InternalErrorException("Error creating preference")

        except Exception as error:
            _logger.error(f"Error on create_preference: {str(error)}")
            raise InternalErrorException("Error creating preference")

    def get_preference(self, preference_id: str) -> MPPreferenceModel:
        """
        Obtém os detalhes de uma preferência de pagamento.
        :param preference_id: ID da preferência.
        """
        _logger.info(f"Calling get_preference - preference_id: {preference_id}")
        try:
            response = self.mp.preference().get(preference_id)

            if response.get("status") == 200:
                return MPPreferenceModel(**response["response"])

            elif response.get("status") == 404:
                _logger.warning(f"Preference {preference_id} NOT found")
                raise NotFoundError(f"Preference {preference_id} not found")

            else:
                _logger.error(f"Error fetching preference - Status: {response.get('status')} - Response: {response.get('response')}")
                raise InternalErrorException(f"Error fetching preference {preference_id}")

        except Exception as error:
            _logger.error(f"Error on get_preference: {str(error)}")
            raise InternalErrorException(f"Error fetching preference {preference_id}")

    def delete_preference(self, preference_id: str) -> bool:
        """
        Deleta (desativa) uma preferência de pagamento. 
        Nota: A API do Mercado Pago não possui um método direto para exclusão, 
        então este método apenas marca como inativa ou verifica se existe.
        :param preference_id: ID da preferência a ser deletada.
        """
        _logger.info(f"Calling delete_preference - preference_id: {preference_id}")
        try:
            # Verifica se a preferência existe antes de tentar manipulá-la
            response = self.mp.preference().get(preference_id)

            if response.get("status") == 404:
                _logger.warning(f"Preference {preference_id} NOT found")
                raise NotFoundError(f"Preference {preference_id} not found")

            elif response.get("status") != 200:
                _logger.error(f"Error fetching preference for deletion - Status: {response.get('status')} - Response: {response.get('response')}")
                raise InternalErrorException(f"Error fetching preference {preference_id} for deletion")

            # A API do Mercado Pago não permite exclusão direta, mas podemos atualizar para desativar
            update_data = {
                "status": "disabled"  # ou outro status que indique desativação, conforme a documentação
            }
            update_response = self.mp.preference().update(preference_id, update_data)

            if update_response.get("status") == 200:
                _logger.info(f"Preference {preference_id} successfully disabled")
                return True
            else:
                _logger.error(f"Error disabling preference - Status: {update_response.get('status')} - Response: {update_response.get('response')}")
                raise InternalErrorException(f"Error disabling preference {preference_id}")

        except Exception as error:
            _logger.error(f"Error on delete_preference: {str(error)}")
            raise InternalErrorException(f"Error deleting preference {preference_id}")
