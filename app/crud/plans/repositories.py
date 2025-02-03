from datetime import datetime
from typing import List
from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository

from .models import PlanModel
from .schemas import Plan, PlanInDB

_logger = get_logger(__name__)


class PlanRepository(Repository):
    async def create(self, plan: Plan) -> PlanInDB:
        try:
            plan_model = PlanModel(
                created_at=datetime.now(),
                updated_at=datetime.now(),
                **plan.model_dump()
            )

            plan_model.save()

            return PlanInDB.model_validate(plan_model)

        except Exception as error:
            _logger.error(f"Error on create_plan: {str(error)}")
            raise UnprocessableEntity(message="Error on create new Plan")

    async def update(self, plan: PlanInDB) -> PlanInDB:
        try:
            plan_model: PlanModel = PlanModel.objects(
                id=plan.id,
                is_active=True,
            ).first()

            plan_model.update(**plan.model_dump())

            return await self.select_by_id(id=plan.id)

        except Exception as error:
            _logger.error(f"Error on update_plan: {str(error)}")
            raise UnprocessableEntity(message="Error on update Plan")

    async def select_by_id(self, id: str, raise_404: bool = True) -> PlanInDB:
        try:
            plan_model: PlanModel = PlanModel.objects(
                id=id,
                is_active=True,
            ).first()

            return PlanInDB.model_validate(plan_model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            if raise_404:
                raise NotFoundError(message=f"Plan #{id} not found")

    async def select_by_name(self, name: str, raise_404: bool = True) -> PlanInDB:
        try:
            plan_model: PlanModel = PlanModel.objects(
                name=name,
                is_active=True,
            ).first()

            return PlanInDB.model_validate(plan_model)

        except Exception as error:
            _logger.error(f"Error on select_by_name: {str(error)}")
            if raise_404:
                raise NotFoundError(message=f"Plan with name {name} not found")

    async def select_all(self) -> List[PlanInDB]:
        try:
            plans = []

            objects = PlanModel.objects(is_active=True)

            for plan_model in objects.order_by("price"):
                plans.append(PlanInDB.model_validate(plan_model))

            return plans

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"Plans not found")

    async def delete_by_id(self, id: str) -> PlanInDB:
        try:
            plan_model: PlanModel = PlanModel.objects(
                id=id,
                is_active=True
            ).first()
            plan_model.delete()

            return PlanInDB.model_validate(plan_model)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Plan #{id} not found")
