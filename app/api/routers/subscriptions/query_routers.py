from fastapi import APIRouter, Depends, Security

from app.api.composers import subscription_composer
from app.api.dependencies import build_response, decode_jwt
from app.builder.subscriptions import SubscriptionBuilder
from app.crud.invoices.schemas import InvoiceInDB
from app.crud.users import CompleteUserInDB

router = APIRouter(tags=["Subscriptions"])


@router.get("/organizations/{organization_id}/subscriptions", responses={200: {"model": InvoiceInDB}})
async def get_subscription_by_id(
    organization_id: str,
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=["subscription:get"]),
    subscription_builder: SubscriptionBuilder = Depends(subscription_composer),
):
    subscription_in_db = await subscription_builder.get_subscription(organization_id=organization_id)

    if subscription_in_db:
        return build_response(
            status_code=200, message="Subscription found with success", data=subscription_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Subscription for organization {organization_id} not found", data=None
        )
