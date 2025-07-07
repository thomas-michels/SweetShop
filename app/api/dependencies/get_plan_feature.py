
import json
from app.api.dependencies.redis_manager import RedisManager
from app.api.exceptions.authentication_exceptions import PaymentRequiredException
from app.core.utils.features import Feature
from app.crud.organization_plans.repositories import OrganizationPlanRepository
from app.crud.plan_features.repositories import PlanFeatureRepository
from app.crud.plan_features.schemas import PlanFeatureInDB
from app.core.configs import get_logger

logger = get_logger(__name__)
redis_manager = RedisManager()


async def get_plan_feature(organization_id: str, feature_name: Feature) -> PlanFeatureInDB:
    cache_key = f"organization:{organization_id}:plan_feature:{feature_name}"

    cached_value = redis_manager.get_value(cache_key)

    if cached_value:
        logger.info(f"Cached feature - {cache_key}")
        return PlanFeatureInDB(**json.loads(cached_value))

    organization_plan_repository = OrganizationPlanRepository(cache_plans={})
    plan_feature_repository = PlanFeatureRepository()

    active_plan = await organization_plan_repository.select_active_plan(
        organization_id=organization_id
    )

    if not active_plan or not active_plan.has_paid_invoice:
        raise PaymentRequiredException()

    plan_feature = await plan_feature_repository.select_by_name(
        name=feature_name,
        plan_id=active_plan.plan_id
    )

    redis_manager.set_value(cache_key, plan_feature.model_dump_json(), expiration=3600)

    return plan_feature
