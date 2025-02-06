from fastapi import Depends
from app.api.composers.invoice_composite import invoice_composer
from app.api.composers.organization_plan_composite import organization_plan_composer
from app.api.composers.plan_composite import plan_composer
from app.builder.subscriptions import SubscriptionBuilder


async def subscription_composer(
    invoice_service = Depends(invoice_composer),
    organization_plan_service = Depends(organization_plan_composer),
    plan_service = Depends(plan_composer),
) -> SubscriptionBuilder:
    subscription_builder = SubscriptionBuilder(
        invoice_service=invoice_service,
        organization_plan_service=organization_plan_service,
        plan_service=plan_service
    )
    return subscription_builder
