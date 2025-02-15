
from app.api.exceptions.authentication_exceptions import PaymentRequiredException
from app.core.utils.features import Feature
from app.crud.organization_plans.repositories import OrganizationPlanRepository
from app.crud.plan_features.repositories import PlanFeatureRepository
from app.crud.plan_features.schemas import PlanFeatureInDB


async def get_plan_feature(organization_id: str, feature_name: Feature) -> PlanFeatureInDB:
    organization_plan_repository = OrganizationPlanRepository()
    plan_feature_repository = PlanFeatureRepository()

    active_plan = await organization_plan_repository.select_active_plan(
        organization_id=organization_id
    )

    if not active_plan.has_paid_invoice:
        raise PaymentRequiredException()

    plan_feature = await plan_feature_repository.select_by_name(name=feature_name)

    return plan_feature
