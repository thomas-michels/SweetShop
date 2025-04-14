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
            organization_plan_model: OrganizationPlanModel = OrganizationPlanModel.objects(
                id=organization_plan.id,
                organization_id=organization_plan.organization_id,
                is_active=True,
            ).first()

            organization_plan_model.update(**organization_plan.model_dump(exclude=["active_plan", "has_paid_invoice"]))

            return await self.select_by_id(id=organization_plan.id)

        except Exception as error:
            _logger.error(f"Error on update_organization_plan: {str(error)}")
            raise UnprocessableEntity(message="Error on update OrganizationPlan")

    async def select_by_id(self, id: str, raise_404: bool = True) -> OrganizationPlanInDB:
        try:
            organization_plan_model: OrganizationPlanModel = OrganizationPlanModel.objects(
                id=id,
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

    async def select_active_plan(self, organization_id: str) -> OrganizationPlanInDB:
        try:
            pipeline = [
                {
                    "$match": {
                        "is_active": True,
                        "organization_id": organization_id
                    }
                },
                {
                    "$lookup": {
                        "from": "invoices",
                        "let": { "orgPlanId": "$_id" },
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {
                                        "$and": [
                                            { "$eq": ["$organization_plan_id", "$$orgPlanId"] },
                                            { "$eq": ["$status", "PAID"] }
                                        ]
                                    }
                                }
                            },
                            { "$limit": 1 }
                        ],
                        "as": "paid_invoice"
                    }
                },
                {
                    "$addFields": {
                        "has_paid_invoice": { "$gt": [{ "$size": "$paid_invoice" }, 0] },
                        "id": "$_id"
                    }
                },
                {
                    "$project": {
                        "paid_invoice": 0,
                        "_id": 0
                    }
                },
                {
                    "$sort": { "end_date": -1 }
                }
            ]

            results = list(OrganizationPlanModel.objects.aggregate(pipeline))

            if not results:
                return

            for organization_plan in results:
                organization_plan_in_db = OrganizationPlanInDB.model_validate(organization_plan)
                if organization_plan_in_db.active_plan:
                    return organization_plan_in_db

        except Exception as error:
            _logger.error(f"Error on select_active_plan: {str(error)}")
            raise NotFoundError(message="OrganizationPlans not found")

    async def check_if_period_is_available(self, start_date: datetime, end_date: datetime, organization_id: str) -> List[OrganizationPlanInDB]:
        existing_plan = OrganizationPlanModel.objects(
            (
                Q(start_date__lte=end_date) &
                Q(end_date__gte=start_date)
            ),
            organization_id=organization_id
        )

        organization_plans = []

        if existing_plan:
            for organization_plan_model in existing_plan.order_by("-end_date"):
                organization_plans.append(OrganizationPlanInDB.model_validate(organization_plan_model))

            return organization_plans
