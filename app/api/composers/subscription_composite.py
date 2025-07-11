from fastapi import Depends
from app.api.composers.coupon_composite import coupon_composer
from app.api.composers.invoice_composite import invoice_composer
from app.api.composers.organization_composite import organization_composer
from app.api.composers.organization_plan_composite import organization_plan_composer
from app.api.composers.plan_composite import plan_composer
from app.api.dependencies.cache_plans import get_cached_plans
from app.builder.subscriptions import SubscriptionBuilder


async def subscription_composer(
    invoice_service = Depends(invoice_composer),
    organization_service = Depends(organization_composer),
    organization_plan_service = Depends(organization_plan_composer),
    plan_service = Depends(plan_composer),
    coupon_service = Depends(coupon_composer),
    cache_plans=Depends(get_cached_plans)
) -> SubscriptionBuilder:
    subscription_builder = SubscriptionBuilder(
        invoice_service=invoice_service,
        organization_service=organization_service,
        organization_plan_service=organization_plan_service,
        plan_service=plan_service,
        coupon_service=coupon_service,
        cache_plans=cache_plans
    )
    return subscription_builder
