from datetime import datetime
from typing import List
from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository
from app.core.utils.features import Feature

from .models import PlanFeatureModel
from .schemas import PlanFeature, PlanFeatureInDB

_logger = get_logger(__name__)


class PlanFeatureRepository(Repository):
    async def create(self, plan_feature: PlanFeature) -> PlanFeatureInDB:
        try:
            existing_feature = PlanFeatureModel.objects(
                plan_id=plan_feature.plan_id,
                name=plan_feature.name.value,
                is_active=True,
            ).first()

            if existing_feature:
                raise UnprocessableEntity(
                    message="This feature already exists for this plan!"
                )

            plan_feature_model = PlanFeatureModel(
                created_at=datetime.now(),
                updated_at=datetime.now(),
                **plan_feature.model_dump(exclude=["display_name", "display_value"])
            )

            plan_feature_model.save()

            return PlanFeatureInDB.model_validate(plan_feature_model)

        except Exception as error:
            _logger.error(f"Error on create_plan_feature: {str(error)}")
            raise UnprocessableEntity(message="Error on create new plan feature")

    async def update(self, plan_feature: PlanFeatureInDB) -> PlanFeatureInDB:
        try:
            plan_feature_model: PlanFeatureModel = PlanFeatureModel.objects(
                id=plan_feature.id,
                is_active=True,
            ).first()

            if not plan_feature_model:
                raise UnprocessableEntity(message="PlanFeature not found or inactive")

            existing_feature = PlanFeatureModel.objects(
                plan_id=plan_feature.plan_id,
                name=plan_feature.name.value,
                is_active=True,
                id__ne=plan_feature.id
            ).first()

            if existing_feature:
                raise UnprocessableEntity(
                    message="This feature already exists for this plan!"
                )

            plan_feature_model.update(**plan_feature.model_dump(exclude=["display_name"]))

            return await self.select_by_id(id=plan_feature.id)

        except Exception as error:
            _logger.error(f"Error on update_plan_feature: {str(error)}")
            raise UnprocessableEntity(message="Error on update PlanFeature")

    async def select_by_id(self, id: str, raise_404: bool = True) -> PlanFeatureInDB:
        try:
            plan_feature_model: PlanFeatureModel = PlanFeatureModel.objects(
                id=id,
                is_active=True,
            ).first()

            return PlanFeatureInDB.model_validate(plan_feature_model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            if raise_404:
                raise NotFoundError(message=f"PlanFeature #{id} not found")

    async def select_by_name(self, name: Feature, plan_id: str, raise_404: bool = True) -> PlanFeatureInDB:
        try:
            plan_feature_model: PlanFeatureModel = PlanFeatureModel.objects(
                name=name.value,
                plan_id=plan_id,
                is_active=True,
            ).first()

            if plan_feature_model:
                return PlanFeatureInDB.model_validate(plan_feature_model)

            elif raise_404:
                raise NotFoundError(message=f"PlanFeature with name {name.value} not found")

        except Exception as error:
            _logger.error(f"Error on select_by_name: {str(error)}")
            if raise_404:
                raise NotFoundError(message=f"PlanFeature with name {name.value} not found")

    async def select_all(self, plan_id: str) -> List[PlanFeatureInDB]:
        try:
            plan_features = []

            objects = PlanFeatureModel.objects(
                plan_id=plan_id,
                is_active=True
            )

            for plan_feature_model in objects:
                plan_features.append(PlanFeatureInDB.model_validate(plan_feature_model))

            return plan_features

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"Plans not found")

    async def delete_by_id(self, id: str) -> PlanFeatureInDB:
        try:
            plan_feature_model: PlanFeatureModel = PlanFeatureModel.objects(
                id=id,
                is_active=True
            ).first()
            plan_feature_model.delete()

            return PlanFeatureInDB.model_validate(plan_feature_model)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"PlanFeature #{id} not found")
