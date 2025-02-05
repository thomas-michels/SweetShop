from app.crud.plan_features.repositories import PlanFeatureRepository
from app.crud.plans.repositories import PlanRepository
from app.crud.plans.services import PlanServices


async def plan_composer() -> PlanServices:
    plan_repository = PlanRepository()
    plan_feature_repository = PlanFeatureRepository()

    plan_services = PlanServices(
        plan_repository=plan_repository,
        plan_feature_repository=plan_feature_repository
    )
    return plan_services
