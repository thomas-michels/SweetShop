from app.crud.plan_features.repositories import PlanFeatureRepository
from app.crud.plan_features.services import PlanFeatureServices
from app.crud.plans.repositories import PlanRepository


async def plan_feature_composer() -> PlanFeatureServices:
    plan_feature_repository = PlanFeatureRepository()
    plan_repository = PlanRepository()

    plan_services = PlanFeatureServices(
        plan_feature_repository=plan_feature_repository,
        plan_repository=plan_repository
    )
    return plan_services
