from app.crud.plans.repositories import PlanRepository
from app.crud.plans.services import PlanServices


async def plan_composer() -> PlanServices:
    plan_repository = PlanRepository()
    plan_services = PlanServices(
        plan_repository=plan_repository
    )
    return plan_services
