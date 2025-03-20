from fastapi import APIRouter, Depends, Query, Request
from app.api.dependencies.validate_x_signature import validate_signature
from app.core.configs import get_logger
from app.api.composers.subscription_composite import subscription_composer
from app.api.dependencies.response import build_response
from app.builder.subscriptions import SubscriptionBuilder

_logger = get_logger(__name__)
router = APIRouter(prefix="/mercado-pago", tags=["Mercado Pago"])


@router.post("/webhook")
async def webhook(
    request: Request,
    event_type: str = Query(alias="type"),
    event_id: str = Query(alias="data.id"),
    subscription_builder: SubscriptionBuilder = Depends(subscription_composer),
):
    """
    Webhook para capturar notificações de pagamento do Mercado Pago.
    """
    if not validate_signature(request):
        _logger.warning("Invalid webhook signature")
        return build_response(status_code=403, message="Invalid signature", data=None)

    data = {}

    subscription_in_db = None

    if event_type == "payment" and event_id:
        subscription_in_db = await subscription_builder.update_payment(
            payment_id=event_id
        )

    elif event_type == "subscription_preapproval" and event_id:
        subscription_in_db = await subscription_builder.update_subscription(
            subscription_id=event_id,
            data=data
        )

    elif event_type == "subscription_authorized_payment" and event_id:
        subscription_in_db = await subscription_builder.update_subscription_payment(
            authorized_payment_id=event_id,
            data=data
        )

    else:
        _logger.warning(f"event_type not recognized - {event_type}")

    if subscription_in_db:
        return build_response(
            status_code=200, message="Subscription updated with success", data=None
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on update a subscription", data=None
        )
