from typing import List

from app.crud.plan_features.repositories import PlanFeatureRepository

from .schemas import Plan, PlanInDB, UpdatePlan, CompletePlanInDB
from .repositories import PlanRepository


class PlanServices:

    def __init__(
            self,
            plan_repository: PlanRepository,
            plan_feature_repository: PlanFeatureRepository
        ) -> None:
        self.__plan_repository = plan_repository
        self.__plan_feature_repository = plan_feature_repository

    async def create(self, plan: Plan) -> PlanInDB:
        plan_in_db = await self.__plan_repository.create(plan=plan)
        return plan_in_db

    async def update(self, id: str, updated_plan: UpdatePlan) -> PlanInDB:
        plan_in_db = await self.search_by_id(id=id)

        is_updated = plan_in_db.validate_updated_fields(update_plan=updated_plan)

        if is_updated:
            plan_in_db = await self.__plan_repository.update(plan=plan_in_db)

        return plan_in_db

    async def search_by_id(self, id: str, expand: List[str] = []) -> PlanInDB | CompletePlanInDB:
        plan_in_db = await self.__plan_repository.select_by_id(id=id)

        if not expand:
            return plan_in_db

        return await self.__mount_complete_plan(plan=plan_in_db, expand=expand)

    async def search_by_name(self, name: str, expand: List[str] = []) -> PlanInDB | CompletePlanInDB:
        plan_in_db = await self.__plan_repository.select_by_name(name=name)

        if not expand:
            return plan_in_db

        return await self.__mount_complete_plan(plan=plan_in_db, expand=expand)

    async def search_all(self, hide: bool = False, expand: List[str] = []) -> List[PlanInDB | CompletePlanInDB]:
        plans = await self.__plan_repository.select_all(hide=hide)

        if not expand:
            return plans

        complete_plans = []

        for plan in plans:
            complete_plans.append(await self.__mount_complete_plan(plan=plan, expand=expand))

        return complete_plans

    async def delete_by_id(self, id: str) -> PlanInDB:
        plan_in_db = await self.__plan_repository.delete_by_id(id=id)
        return plan_in_db

    async def __mount_complete_plan(self, plan: PlanInDB, expand: List[str]) -> CompletePlanInDB:
        complete_plan_in_db = CompletePlanInDB.model_validate(plan)

        if "features" in expand:
            plan_features = await self.__plan_feature_repository.select_all(plan_id=plan.id)
            complete_plan_in_db.features = plan_features

        return complete_plan_in_db
