from datetime import datetime, timedelta
from app.api.dependencies.mercado_pago_integration import MercadoPagoIntegration
from app.api.shared_schemas.subscription import RequestSubscription, ResponseSubscription
from app.crud.invoices.schemas import Invoice
from app.crud.invoices.services import InvoiceServices
from app.crud.organization_plans.schemas import OrganizationPlan, OrganizationPlanInDB
from app.crud.organization_plans.services import OrganizationPlanServices
from app.crud.plans.services import PlanServices
from app.crud.users.schemas import UserInDB


class SubscriptionBuilder:

    def __init__(
            self,
            invoice_service: InvoiceServices,
            plan_service: PlanServices,
            organization_plan_service: OrganizationPlanServices,
        ) -> None:
        self.__invoice_service = invoice_service
        self.__plan_service = plan_service
        self.__organization_plan_service = organization_plan_service
        self.__mp_integration = MercadoPagoIntegration()

    async def subscribe(self, subscription: RequestSubscription, user: UserInDB) -> ResponseSubscription:
        plan_in_db = await self.__plan_service.search_by_id(id=subscription.plan_id)
        annual_price = round(plan_in_db.price * 12, 2)

        organization_plan_in_db = await self.__create_organization_plan(subscription)

        mp_sub = self.__mp_integration.create_subscription(
            reason=f"pedidoZ - {plan_in_db.name}",
            price_monthly=plan_in_db.price,
            user_info={
                "email": user.email,
                "nome": user.name
            }
        )

        invoice = Invoice(
            organization_plan_id=organization_plan_in_db.id,
            integration_id=mp_sub.id,
            integration_type="mercado-pago",
            amount=annual_price
        )

        invoice_in_db = await self.__invoice_service.create(
            invoice=invoice,
            organization_id=subscription.organization_id
        )

        return ResponseSubscription(
            invoice_id=invoice_in_db.id,
            integration_id=mp_sub.id,
            init_point=mp_sub.init_point,
        )

    async def get_subscription(self, subscription_id: str):
        ...

    async def unsubscribe(self, subscription_id: str):
        ...

    async def __create_organization_plan(self, subscription: RequestSubscription) -> OrganizationPlanInDB:
        now = datetime.now()
        today = datetime(year=now.year, month=now.month, day=now.day)
        sub_end = today + timedelta(days=365)

        organization_plan = OrganizationPlan(
            plan_id=subscription.plan_id,
            allow_additional=subscription.allow_additional,
            start_date=today,
            end_date=sub_end
        )

        organization_plan_in_db = await self.__organization_plan_service.create(
            organization_plan=organization_plan,
            organization_id=subscription.organization_id
        )

        return organization_plan_in_db
