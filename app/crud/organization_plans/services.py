from typing import List

from app.crud.plans.repositories import PlanRepository

from .schemas import OrganizationPlan, OrganizationPlanInDB, UpdateOrganizationPlan
from .repositories import OrganizationPlanRepository


class OrganizationPlanServices:

    def __init__(
        self,
        organization_plan_repository: OrganizationPlanRepository,
        plan_repository: PlanRepository,
    ) -> None:
        self.__organization_plan_repository = organization_plan_repository
        self.__plan_repository = plan_repository

    async def create(self, organization_plan: OrganizationPlan, organization_id: str) -> OrganizationPlanInDB:
        if organization_plan.plan_id:
            await self.__plan_repository.select_by_id(id=organization_plan.plan_id)

        organization_plan_in_db = await self.__organization_plan_repository.create(
            organization_plan=organization_plan,
            organization_id=organization_id
        )
        return organization_plan_in_db

    async def update(self, id: str, organization_id: str, updated_organization_plan: UpdateOrganizationPlan) -> OrganizationPlanInDB:
        organization_plan_in_db = await self.search_by_id(id=id, organization_id=organization_id)

        is_updated = organization_plan_in_db.validate_updated_fields(update_organization_plan=updated_organization_plan)

        if is_updated:
            organization_plan_in_db = await self.__organization_plan_repository.update(organization_plan=organization_plan_in_db)

        return organization_plan_in_db

    async def search_by_id(self, id: str, organization_id: str) -> OrganizationPlanInDB:
        organization_plan_in_db = await self.__organization_plan_repository.select_by_id(id=id, organization_id=organization_id)
        return organization_plan_in_db

    async def search_active_plan(self, organization_id: str) -> OrganizationPlanInDB:
        organization_plan = await self.__organization_plan_repository.select_active_plan(organization_id=organization_id)
        return organization_plan

    async def search_all(self, organization_id: str) -> List[OrganizationPlanInDB]:
        organization_plans = await self.__organization_plan_repository.select_all(organization_id=organization_id)
        return organization_plans

    async def delete_by_id(self, id: str, organization_id: str) -> OrganizationPlanInDB:
        organization_plan_in_db = await self.__organization_plan_repository.delete_by_id(id=id, organization_id=organization_id)
        return organization_plan_in_db
