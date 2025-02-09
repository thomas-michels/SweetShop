from datetime import datetime, timedelta
from app.api.dependencies.mercado_pago_integration import MercadoPagoIntegration
from app.api.shared_schemas.subscription import RequestSubscription, ResponseSubscription
from app.crud.invoices.schemas import Invoice, InvoiceInDB, InvoiceStatus, UpdateInvoice
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

        invoice_in_db = await self.__check_if_has_pending_payment(
            organization_id=subscription.organization_id
        )

        if invoice_in_db:
            mp_sub = self.__mp_integration.create_subscription(
                reason=f"pedidoZ - {plan_in_db.name}",
                price_monthly=plan_in_db.price,
                user_info={
                    "email": user.email,
                    "nome": user.name
                }
            )

            invoice_in_db.status = InvoiceStatus.PENDING
            invoice_in_db.integration_id = mp_sub.id

            invoice_in_db = await self.__invoice_service.update(
                id=invoice_in_db.id,
                updated_invoice=invoice_in_db
            )

        else:
            organization_plan_in_db = await self.__create_organization_plan(
                subscription=subscription
            )

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
                amount=annual_price,
                observation={}
            )

            invoice_in_db = await self.__invoice_service.create(
                invoice=invoice,
                organization_id=subscription.organization_id
            )

        print(f"MP Sub - {mp_sub.model_dump_json()}")

        return ResponseSubscription(
            invoice_id=invoice_in_db.id,
            integration_id=mp_sub.id,
            init_point=mp_sub.init_point,
        )

    async def update_payment(self, payment_id: str) -> InvoiceInDB:
        payment_data = self.__mp_integration.get_payment(payment_id)
        payment_status = payment_data.get("status")

        status_map = {
            "approved": InvoiceStatus.PAID,
            "pending": InvoiceStatus.PENDING,
            "rejected": InvoiceStatus.REJECTED,
            "cancelled": InvoiceStatus.CANCELLED
        }

        internal_status = status_map.get(payment_status)

        invoice_in_db = await self.__invoice_service.search_by_integration(
            integration_id=payment_id,
            integration_type="mercado-pago"
        )

        update_invoice = UpdateInvoice(
            status=internal_status
        )

        if internal_status == InvoiceStatus.PAID:
            update_invoice.paid_at = datetime.now()
            update_invoice.amount_paid = invoice_in_db.amount

        updated_invoice = await self.__invoice_service.update(
            id=invoice_in_db.id,
            updated_invoice=update_invoice
        )

        return updated_invoice

    async def get_subscription(self, organization_id: str) -> InvoiceInDB:
        organization_plan_in_db = await self.__organization_plan_service.search_active_plan(organization_id=organization_id)

        invoice_in_db = await self.__invoice_service.search_by_organization_plan_id(
            organization_plan_id=organization_plan_in_db.id
        )

        return invoice_in_db

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

    async def __check_if_has_pending_payment(self, organization_id: str) -> InvoiceInDB:
        organization_plan = await self.__organization_plan_service.search_active_plan(
            organization_id=organization_id
        )

        if organization_plan:
            invoice_in_db = await self.__invoice_service.search_by_organization_plan_id(
                organization_plan_id=organization_plan.id,
                raise_404=False
            )

            if invoice_in_db and invoice_in_db.status != InvoiceStatus.PAID:
                return invoice_in_db
