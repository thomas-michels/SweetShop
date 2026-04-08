from fastapi import Depends

from app.api.dependencies.cache_plans import get_cached_plans
from app.api.dependencies.cache_users import get_cached_complete_users, get_cached_users
from app.api.dependencies.get_access_token import get_access_token
from app.api.composers.marketing_email_composite import marketing_email_composer
from app.crud.addresses.repositories import AddressRepository
from app.crud.addresses.services import AddressServices
from app.crud.invoices.repositories import InvoiceRepository
from app.crud.invoices.services import InvoiceServices
from app.crud.organization_plans.repositories import OrganizationPlanRepository
from app.crud.organization_plans.services import OrganizationPlanServices
from app.crud.organizations.repositories import OrganizationRepository
from app.crud.organizations.services import OrganizationServices
from app.crud.plan_features.repositories import PlanFeatureRepository
from app.crud.plans.repositories import PlanRepository
from app.crud.plans.services import PlanServices
from app.crud.users.repositories import UserRepository


async def organization_composer(
    access_token=Depends(get_access_token),
    cached_complete_users=Depends(get_cached_complete_users),
    cached_users=Depends(get_cached_users),
    cache_plans=Depends(get_cached_plans),
) -> OrganizationServices:
    organization_repository = OrganizationRepository()
    user_repository = UserRepository(
        access_token=access_token,
        cache_users=cached_users
    )

    organization_plan_repository = OrganizationPlanRepository(
        cache_plans=cache_plans
    )
    plan_repository = PlanRepository()
    plan_feature_repository = PlanFeatureRepository()

    address_services = AddressServices(
        address_repository=AddressRepository()
    )

    plan_services = PlanServices(
        plan_repository=plan_repository,
        plan_feature_repository=plan_feature_repository,
    )

    organization_plan_services = OrganizationPlanServices(
        organization_plan_repository=organization_plan_repository,
        plan_repository=plan_repository,
    )

    invoice_services = InvoiceServices(
        invoice_repository=InvoiceRepository(),
        organization_plan_repository=organization_plan_repository,
    )

    marketing_email_services = await marketing_email_composer()

    organization_services = OrganizationServices(
        organization_repository=organization_repository,
        organization_plan_repository=organization_plan_repository,
        address_services=address_services,
        user_repository=user_repository,
        cached_complete_users=cached_complete_users,
        plan_services=plan_services,
        organization_plan_services=organization_plan_services,
        invoice_services=invoice_services,
        marketing_email_services=marketing_email_services,
    )
    return organization_services
