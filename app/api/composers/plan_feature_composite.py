from app.crud.plan_features.repositories import PlanFeatureRepository
from app.crud.plan_features.services import PlanFeatureServices


async def plan_feature_composer() -> PlanFeatureServices:
    plan_feature_repository = PlanFeatureRepository()
    plan_services = PlanFeatureServices(
        plan_feature_repository=plan_feature_repository
    )
    return plan_services
