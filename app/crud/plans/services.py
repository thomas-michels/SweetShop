from typing import List

from .schemas import Plan, PlanInDB, UpdatePlan
from .repositories import PlanRepository


class PlanServices:

    def __init__(self, plan_repository: PlanRepository) -> None:
        self.__plan_repository = plan_repository

    async def create(self, plan: Plan) -> PlanInDB:
        plan_in_db = await self.__plan_repository.create(plan=plan)
        return plan_in_db

    async def update(self, id: str, updated_plan: UpdatePlan) -> PlanInDB:
        plan_in_db = await self.search_by_id(id=id)

        is_updated = plan_in_db.validate_updated_fields(update_plan=updated_plan)

        if is_updated:
            plan_in_db = await self.__plan_repository.update(plan=plan_in_db)

        return plan_in_db

    async def search_by_id(self, id: str) -> PlanInDB:
        plan_in_db = await self.__plan_repository.select_by_id(id=id)
        return plan_in_db

    async def search_by_name(self, name: str) -> PlanInDB:
        plan_in_db = await self.__plan_repository.select_by_name(name=name)
        return plan_in_db

    async def search_all(self) -> List[PlanInDB]:
        plans = await self.__plan_repository.select_all()
        return plans

    async def delete_by_id(self, id: str) -> PlanInDB:
        plan_in_db = await self.__plan_repository.delete_by_id(id=id)
        return plan_in_db
