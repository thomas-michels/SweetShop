from fastapi import APIRouter, Depends, Security

from app.api.composers import subscription_composer
from app.api.dependencies import build_response, decode_jwt
from app.builder.subscriptions import SubscriptionBuilder
from app.crud.users import CompleteUserInDB

router = APIRouter(tags=["Subscriptions"])


@router.get("/subscriptions/{subscription_id}",) # responses={200: {"model": }})
async def get_subscription_by_id(
    subscription_id: str,
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=["subscription:get"]),
    subscription_builder: SubscriptionBuilder = Depends(subscription_composer),
):
    subscription_in_db = await subscription_builder.get_subscription(subscription_id=subscription_id)

    if subscription_in_db:
        return build_response(
            status_code=200, message="Subscription found with success", data=subscription_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Subscription {subscription_id} not found", data=None
        )
