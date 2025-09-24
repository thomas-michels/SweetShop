from fastapi import Depends

from app.api.dependencies.get_current_organization import check_current_organization
from app.crud.business_days.repositories import BusinessDayRepository
from app.crud.business_days.services import BusinessDayServices


async def business_day_composer(
    organization_id: str = Depends(check_current_organization),
) -> BusinessDayServices:
    business_day_repository = BusinessDayRepository(organization_id=organization_id)
    business_day_services = BusinessDayServices(
        business_day_repository=business_day_repository
    )
    return business_day_services
