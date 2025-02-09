from datetime import datetime
from mongoengine import Q
from typing import List
from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository

from .models import OrganizationPlanModel
from .schemas import OrganizationPlan, OrganizationPlanInDB

_logger = get_logger(__name__)


class OrganizationPlanRepository(Repository):
    async def create(self, organization_plan: OrganizationPlan, organization_id: str) -> OrganizationPlanInDB:
        try:
            await self.__check_if_is_duplicated(
                organization_plan=organization_plan,
                organization_id=organization_id
            )

            organization_plan_model = OrganizationPlanModel(
                organization_id=organization_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                **organization_plan.model_dump()
            )

            organization_plan_model.save()

            return OrganizationPlanInDB.model_validate(organization_plan_model)

        except UnprocessableEntity as error:
            raise error

        except Exception as error:
            _logger.error(f"Error on create_organization_plan: {str(error)}")
            raise UnprocessableEntity(message="Error on create new OrganizationPlan")

    async def update(self, organization_plan: OrganizationPlanInDB) -> OrganizationPlanInDB:
        try:
            conflicting_plan = OrganizationPlanModel.objects(
                (
                    Q(start_date__lt=organization_plan.end_date) &
                    Q(end_date__gt=organization_plan.start_date)
                ),
                id__ne=organization_plan.id,
                organization_id=organization_plan.organization_id,
            ).first()

            if conflicting_plan:
                raise UnprocessableEntity(message="There is already an active plan for this period")

            organization_plan_model: OrganizationPlanModel = OrganizationPlanModel.objects(
                id=organization_plan.id,
                organization_id=organization_plan.organization_id,
                is_active=True,
            ).first()

            organization_plan_model.update(**organization_plan.model_dump(exclude=["active_plan"]))

            return await self.select_by_id(
                id=organization_plan.id,
                organization_id=organization_plan.organization_id
            )

        except Exception as error:
            _logger.error(f"Error on update_organization_plan: {str(error)}")
            raise UnprocessableEntity(message="Error on update OrganizationPlan")

    async def select_by_id(self, id: str, organization_id: str, raise_404: bool = True) -> OrganizationPlanInDB:
        try:
            organization_plan_model: OrganizationPlanModel = OrganizationPlanModel.objects(
                id=id,
                organization_id=organization_id,
                is_active=True,
            ).first()

            return OrganizationPlanInDB.model_validate(organization_plan_model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            if raise_404:
                raise NotFoundError(message=f"OrganizationPlan #{id} not found")

    async def select_all(self, organization_id: str) -> List[OrganizationPlanInDB]:
        try:
            organization_plans = []

            objects = OrganizationPlanModel.objects(
                is_active=True,
                organization_id=organization_id
            )

            for organization_plan_model in objects.order_by("-end_date"):
                organization_plans.append(OrganizationPlanInDB.model_validate(organization_plan_model))

            return organization_plans

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"OrganizationPlans not found")

    async def delete_by_id(self, id: str, organization_id) -> OrganizationPlanInDB:
        try:
            organization_plan_model: OrganizationPlanModel = OrganizationPlanModel.objects(
                id=id,
                organization_id=organization_id,
                is_active=True
            ).first()
            organization_plan_model.delete()

            return OrganizationPlanInDB.model_validate(organization_plan_model)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"OrganizationPlan #{id} not found")

    async def __check_if_is_duplicated(self, organization_plan: OrganizationPlan, organization_id: str) -> None:
        existing_plan = OrganizationPlanModel.objects(
            (
                Q(start_date__lte=organization_plan.end_date) &
                Q(end_date__gte=organization_plan.start_date)
            ),
            organization_id=organization_id
        ).first()

        if existing_plan:
            raise UnprocessableEntity(message="There is already an active plan for this period")
