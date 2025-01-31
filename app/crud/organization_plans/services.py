from typing import List

from .schemas import OrganizationPlan, OrganizationPlanInDB, UpdateOrganizationPlan
from .repositories import OrganizationPlanRepository


class OrganizationPlanServices:

    def __init__(self, organization_plan_repository: OrganizationPlanRepository) -> None:
        self.__repository = organization_plan_repository

    async def create(self, organization_plan: OrganizationPlan) -> OrganizationPlanInDB:
        organization_plan_in_db = await self.__repository.create(organization_plan=organization_plan)
        return organization_plan_in_db

    async def update(self, id: str, updated_organization_plan: UpdateOrganizationPlan) -> OrganizationPlanInDB:
        organization_plan_in_db = await self.search_by_id(id=id)

        is_updated = organization_plan_in_db.validate_updated_fields(update_organization_plan=updated_organization_plan)

        if is_updated:
            organization_plan_in_db = await self.__repository.update(organization_plan=organization_plan_in_db)

        return organization_plan_in_db

    async def search_by_id(self, id: str) -> OrganizationPlanInDB:
        organization_plan_in_db = await self.__repository.select_by_id(id=id)
        return organization_plan_in_db

    async def search_all(self) -> List[OrganizationPlanInDB]:
        organization_plans = await self.__repository.select_all()
        return organization_plans

    async def delete_by_id(self, id: str) -> OrganizationPlanInDB:
        organization_plan_in_db = await self.__repository.delete_by_id(id=id)
        return organization_plan_in_db
