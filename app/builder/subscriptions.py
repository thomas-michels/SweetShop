from datetime import datetime, timedelta
from app.api.dependencies.mercado_pago_integration import MercadoPagoIntegration
from app.api.shared_schemas.mercado_pago import MPSubscriptionModel
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

        organization_plan_in_db = await self.__organization_plan_service.search_active_plan(
            organization_id=subscription.organization_id
        )

        if organization_plan_in_db:
            await self.__cancel_pending_payments(
                organization_plan_id=organization_plan_in_db.id
            )

        organization_plan_in_db = await self.__create_or_update_organization_plan(
            subscription=subscription
        )

        mp_sub = self.__mp_integration.create_subscription(
            reason=f"pedidoZ - {plan_in_db.name}",
            price_monthly=plan_in_db.price,
            user_info={
                "email": user.email,
                "name": user.name
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

        return ResponseSubscription(
            invoice_id=invoice_in_db.id,
            integration_id=mp_sub.id,
            init_point=mp_sub.init_point,
        )

    async def update_subscription(self, subscription_id: str, data: dict) -> InvoiceInDB:
        print(f"subscription_id: {subscription_id}")
        print(f"data: {data}")

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
        integration_id = payment_data["metadata"]["preapproval_id"]

        invoice_in_db = await self.__invoice_service.search_by_integration(
            integration_id=integration_id,
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

    async def get_subscription(self, organization_id: str) -> MPSubscriptionModel:
        invoice_in_db = await self.__get_active_invoice(organization_id=organization_id)

        if invoice_in_db:
            mp_sub = self.__mp_integration.get_subscription(preapproval_id=invoice_in_db.integration_id)
            return mp_sub

    async def unsubscribe(self, organization_id: str) -> MPSubscriptionModel:
        invoice_in_db = await self.__get_active_invoice(organization_id=organization_id)

        if invoice_in_db:
            mp_sub = self.__mp_integration.cancel_subscription(preapproval_id=invoice_in_db.integration_id)
            return mp_sub

    async def __create_or_update_organization_plan(self, subscription: RequestSubscription) -> OrganizationPlanInDB:
        now = datetime.now()
        today = datetime(year=now.year, month=now.month, day=now.day)
        sub_end = today + timedelta(days=365)
        organization_plan_in_db = await self.__organization_plan_service.search_active_plan(
            organization_id=subscription.organization_id
        )

        if organization_plan_in_db:
            organization_plan_in_db.start_date = today
            organization_plan_in_db.end_date = sub_end
            organization_plan_in_db.allow_additional = subscription.allow_additional
            organization_plan_in_db.plan_id = subscription.plan_id

            organization_plan_in_db = await self.__organization_plan_service.update(
                id=organization_plan_in_db.id,
                organization_id=organization_plan_in_db.organization_id,
                updated_organization_plan=organization_plan_in_db
            )

        else:
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

    async def __cancel_pending_payments(self, organization_plan_id: str) -> bool:
        invoices = await self.__invoice_service.search_by_organization_plan_id(
            organization_plan_id=organization_plan_id
        )

        for invoice_in_db in invoices:
            if invoice_in_db and invoice_in_db.status not in [InvoiceStatus.CANCELLED, InvoiceStatus.PAID]:
                invoice_in_db.status = InvoiceStatus.CANCELLED

                invoice_in_db = await self.__invoice_service.update(
                    id=invoice_in_db.id,
                    updated_invoice=invoice_in_db
                )

        return True

    async def __get_active_invoice(self, organization_id: str) -> InvoiceInDB:
        organization_plan_in_db = await self.__organization_plan_service.search_active_plan(
            organization_id=organization_id
        )

        invoices = await self.__invoice_service.search_by_organization_plan_id(
            organization_plan_id=organization_plan_in_db.id
        )

        for invoice_in_db in invoices:
            if invoice_in_db.status == InvoiceStatus.PAID:
                return invoice_in_db
