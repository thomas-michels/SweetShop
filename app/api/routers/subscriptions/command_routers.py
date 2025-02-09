from fastapi import APIRouter, Depends, Security

from app.api.composers import subscription_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.shared_schemas.subscription import RequestSubscription, ResponseSubscription
from app.builder.subscriptions import SubscriptionBuilder
from app.crud.users import UserInDB

router = APIRouter(tags=["Subscriptions"])


@router.post("/subscriptions", responses={201: {"model": ResponseSubscription}})
async def create_subscription(
    subscription: RequestSubscription,
    current_user: UserInDB = Security(decode_jwt, scopes=["subscription:create"]),
    subscription_builder: SubscriptionBuilder = Depends(subscription_composer),
):
    subscription_in_db = await subscription_builder.subscribe(
        subscription=subscription,
        user=current_user
    )

    if subscription_in_db:
        return build_response(
            status_code=201, message="Subscription created with success", data=subscription_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on create a subscription", data=None
        )


@router.delete("/organizations/{organization_id}/subscriptions", responses={200: {"model": RequestSubscription}})
async def delete_product(
    organization_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["subscription:delete"]),
    subscription_builder: SubscriptionBuilder = Depends(subscription_composer),
):
    subscription_in_db = await subscription_builder.unsubscribe(organization_id=organization_id)

    if subscription_in_db:
        return build_response(
            status_code=200, message="Subscription deleted with success", data=subscription_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Subscription for organization {organization_id} not found", data=None
        )
