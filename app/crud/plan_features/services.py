from typing import List

from .schemas import PlanFeature, PlanFeatureInDB, UpdatePlanFeature
from .repositories import PlanFeatureRepository


class PlanFeatureServices:

    def __init__(
            self,
            plan_feature_repository: PlanFeatureRepository
        ) -> None:
        self.__plan_feature_repository = plan_feature_repository

    async def create(self, plan_feature: PlanFeature) -> PlanFeatureInDB:
        plan_feature_in_db = await self.__plan_feature_repository.create(plan_feature=plan_feature)
        return plan_feature_in_db

    async def update(self, id: str, updated_plan_feature: UpdatePlanFeature) -> PlanFeatureInDB:
        plan_feature_in_db = await self.search_by_id(id=id)

        is_updated = plan_feature_in_db.validate_updated_fields(update_plan_feature=updated_plan_feature)

        if is_updated:
            plan_feature_in_db = await self.__plan_feature_repository.update(plan_feature=plan_feature_in_db)

        return plan_feature_in_db

    async def search_by_id(self, id: str) -> PlanFeatureInDB:
        plan_feature_in_db = await self.__plan_feature_repository.select_by_id(id=id)
        return plan_feature_in_db

    async def search_all(self, plan_id: str) -> List[PlanFeatureInDB]:
        plan_features = await self.__plan_feature_repository.select_all(plan_id=plan_id)
        return plan_features

    async def delete_by_id(self, id: str) -> PlanFeatureInDB:
        plan_feature_in_db = await self.__plan_feature_repository.delete_by_id(id=id)
        return plan_feature_in_db
