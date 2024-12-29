from fastapi import Depends
from app.api.dependencies.get_current_organization import check_current_organization
from app.crud.tags.repositories import TagRepository
from app.crud.expenses.repositories import ExpenseRepository
from app.crud.expenses.services import ExpenseServices


async def expense_composer(
    organization_id: str = Depends(check_current_organization)
) -> ExpenseServices:
    tag_repository = TagRepository(organization_id=organization_id)
    expense_repository = ExpenseRepository(organization_id=organization_id)
    expense_services = ExpenseServices(
        expense_repository=expense_repository,
        tag_repository=tag_repository
    )
    return expense_services
