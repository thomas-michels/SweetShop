from datetime import datetime, timedelta
from typing import List
from uuid import uuid4
from app.api.dependencies.mercado_pago_integration import MercadoPagoIntegration
from app.api.exceptions.authentication_exceptions import BadRequestException
from app.api.shared_schemas.mercado_pago import MPPreferenceModel
from app.api.shared_schemas.subscription import RequestSubscription, ResponseSubscription
from app.core.utils.get_start_and_end_day_of_month import get_start_and_end_day_of_month
from app.crud.coupons.services import CouponServices
from app.crud.invoices.schemas import Invoice, InvoiceInDB, InvoiceStatus, UpdateInvoice
from app.crud.invoices.services import InvoiceServices
from app.crud.organization_plans.schemas import OrganizationPlan, OrganizationPlanInDB
from app.crud.organization_plans.services import OrganizationPlanServices
from app.crud.organizations.services import OrganizationServices
from app.crud.plans.services import PlanServices
from app.crud.users.schemas import UserInDB
from app.core.configs import get_logger

_logger = get_logger(__name__)


class SubscriptionBuilder:

    def __init__(
            self,
            invoice_service: InvoiceServices,
            organization_service: OrganizationServices,
            plan_service: PlanServices,
            organization_plan_service: OrganizationPlanServices,
            coupon_service: CouponServices,
        ) -> None:
        self.__invoice_service = invoice_service
        self.__organization_service = organization_service
        self.__plan_service = plan_service
        self.__organization_plan_service = organization_plan_service
        self.__coupon_service = coupon_service
        self.__mp_integration = MercadoPagoIntegration()

    async def subscribe(self, subscription: RequestSubscription, user: UserInDB) -> ResponseSubscription:
        plan_in_db = await self.__plan_service.search_by_id(id=subscription.plan_id)

        months_multiplier = subscription.get_sub_months()

        sub_price = round(plan_in_db.price * months_multiplier, 2)

        organization_plan_in_db = await self.__organization_plan_service.search_active_plan(
            organization_id=subscription.organization_id
        )

        if organization_plan_in_db:
            await self.__cancel_pending_payments(
                organization_plan_id=organization_plan_in_db.id
            )

        organization_in_db = await self.__organization_service.search_by_id(
            id=subscription.organization_id
        )

        organization_plan_in_db = await self.__create_or_update_organization_plan(
            subscription=subscription, months_multiplier=months_multiplier
        )

        user_info = {
            "email": organization_in_db.email if organization_in_db.email else user.email,
            "name": user.name
        }

        discount = 0
        observation = {}

        if subscription.cupoun_id:
            coupon_in_db = await self.__coupon_service.search_by_id(id=subscription.cupoun_id)

            coupon_in_db = await self.__coupon_service.update_usage(
                coupon_id=coupon_in_db.id,
                quantity=1
            )

            discount = coupon_in_db.calculate_discount(price=sub_price)

            _logger.info(f"Generating R${discount} of discount using coupon {subscription.cupoun_id}")

            observation["discount"] = discount
            observation["coupon_id"] = subscription.cupoun_id

        label = subscription.get_label()

        if sub_price > 0:
            mp_preference = self.__mp_integration.create_preference(
                reason=f"pedidoZ - Assinatura {label} - {plan_in_db.name}",
                price_monthly=sub_price,
                discount=discount,
                user_info=user_info,
            )
            external_reference = mp_preference.external_reference
            init_point = mp_preference.init_point

        else:
            external_reference = str(uuid4())
            init_point = "https://www.pedidoz.online/organizacoes"

        invoice = Invoice(
            organization_plan_id=organization_plan_in_db.id,
            integration_id=external_reference,
            integration_type="mercado-pago",
            amount=max(sub_price - discount, 0),
            observation=observation
        )

        if sub_price == 0:
            invoice.status = InvoiceStatus.PAID
            invoice.amount_paid = 0

        invoice_in_db = await self.__invoice_service.create(
            invoice=invoice,
            organization_id=subscription.organization_id
        )

        return ResponseSubscription(
            invoice_id=invoice_in_db.id,
            integration_id=external_reference,
            init_point=init_point,
            email=user_info["email"]
        )

    async def recreate_subscription(self, subscription: RequestSubscription, user: UserInDB) -> ResponseSubscription:
        plan_in_db = await self.__plan_service.search_by_id(id=subscription.plan_id)

        months_multiplier = subscription.get_sub_months()

        sub_price = round(plan_in_db.price * months_multiplier, 2)

        organization_plan_in_db = await self.__organization_plan_service.search_active_plan(
            organization_id=subscription.organization_id
        )

        if subscription.cupoun_id is not None:
            raise BadRequestException("You cannot use coupons when you are updating your plan")

        if not organization_plan_in_db:
            _logger.warning(f"Organization {subscription.organization_id} without an active plan")
            return

        if organization_plan_in_db.plan_id == subscription.plan_id:
            raise BadRequestException("You cannot update the organization plan with the same plan")

        await self.__cancel_pending_payments(organization_plan_id=organization_plan_in_db.id)

        # Calculating remaining credits
        old_invoices = await self.__invoice_service.search_by_organization_plan_id(
            organization_plan_id=organization_plan_in_db.id
        )

        old_invoice_in_db = self._get_invoice(invoices=old_invoices)

        credits = 0

        old_plan_in_db = await self.__plan_service.search_by_id(id=organization_plan_in_db.plan_id)

        if old_invoice_in_db and old_plan_in_db.price > 0:

            credits = self._calculate_remaining_credits(
                organization_plan=organization_plan_in_db,
                amount_paid=old_invoice_in_db.amount_paid
            )

            _logger.info(f"R${credits} were generated for the next plan - organization {subscription.organization_id}")

            # Adjusting current organization plan to the end of the month
            organization_plan_in_db.end_date = self._adjust_end_date(organization_plan_in_db.end_date)
            organization_plan_in_db = await self.__organization_plan_service.update(
                id=organization_plan_in_db.id,
                organization_id=organization_plan_in_db.organization_id,
                updated_organization_plan=organization_plan_in_db
            )
            _logger.info(f"Organization plan set to finish on {organization_plan_in_db.end_date}")

            # Getting next plan dates (Next month)
            start_date, end_date = self._get_next_plan_dates(
                reference_date=organization_plan_in_db.end_date,
                months=months_multiplier
            )

            organization_plan_in_db = await self.__create_or_update_organization_plan(
                subscription=subscription,
                months_multiplier=months_multiplier,
                start_date=start_date,
                end_date=end_date
            )

        else:
            # Updating plan not payed yet
            organization_plan_in_db.plan_id = subscription.plan_id
            organization_plan_in_db.end_date = datetime.now() + timedelta(days=30 * months_multiplier)

            organization_plan_in_db = await self.__organization_plan_service.update(
                id=organization_plan_in_db.id,
                organization_id=organization_plan_in_db.organization_id,
                updated_organization_plan=organization_plan_in_db
            )

            _logger.info(f"Organization plan updated to finish on {organization_plan_in_db.end_date}")

        organization_in_db = await self.__organization_service.search_by_id(
            id=subscription.organization_id
        )

        user_info = {
            "email": organization_in_db.email if organization_in_db.email else user.email,
            "name": user.name
        }

        label = subscription.get_label()

        mp_sub = self.__mp_integration.create_preference(
            reason=f"pedidoZ - Assinatura {label} - {plan_in_db.name}",
            price_monthly=sub_price,
            discount=credits,
            user_info=user_info
        )

        invoice = Invoice(
            organization_plan_id=organization_plan_in_db.id,
            integration_id=mp_sub.external_reference,
            integration_type="mercado-pago",
            amount=max(sub_price - credits, 0),
            observation={"credits": credits}
        )

        invoice_in_db = await self.__invoice_service.create(
            invoice=invoice,
            organization_id=subscription.organization_id
        )

        return ResponseSubscription(
            invoice_id=invoice_in_db.id,
            integration_id=mp_sub.external_reference,
            init_point=mp_sub.init_point,
            email=user_info["email"]
        )

    def _calculate_remaining_credits(self, organization_plan: OrganizationPlan, amount_paid: float) -> float:
        """Calcula os créditos restantes com base no tempo restante do plano."""
        today = datetime.today()
        if not amount_paid:
            amount_paid = 0

        remaining_days = (organization_plan.end_date - today).days
        total_days = (organization_plan.end_date - organization_plan.start_date).days

        if total_days <= 0:
            return 0

        return round((remaining_days / total_days) * amount_paid, 2)

    def _adjust_end_date(self, current_end_date: datetime) -> datetime:
        """Ajusta a data de término do plano para o final do mês, se necessário."""
        end_of_month = self._get_end_of_current_month()
        return min(current_end_date, end_of_month)

    def _get_next_plan_dates(self, reference_date: datetime, months: int) -> tuple:
        """Obtém a data de início e fim do próximo plano."""
        next_month = reference_date.month % 12 + 1
        next_year = reference_date.year if next_month > 1 else reference_date.year + 1
        start_date, end_date = get_start_and_end_day_of_month(year=next_year, month=next_month)
        return start_date, end_date + timedelta(days=30 * months)

    def _get_end_of_current_month(self) -> datetime:
        """Retorna a data do último dia do mês atual."""
        today = datetime.today()
        next_month = today.replace(day=28) + timedelta(days=4)  # Garante que passamos para o próximo mês
        day = (next_month - timedelta(days=next_month.day))
        return datetime(
            year=day.year,
            month=day.month,
            day=day.day,
            hour=23,
            minute=59,
            second=59
        )

    def _get_invoice(self, invoices: List[InvoiceInDB]) -> InvoiceInDB:
        for old_invoice_in_db in invoices:
            if old_invoice_in_db.status == InvoiceStatus.PAID:
                return old_invoice_in_db

    async def update_subscription(self, subscription_id: str, data: dict) -> InvoiceInDB:
        mp_sub = self.__mp_integration.get_subscription(preapproval_id=subscription_id)
        invoice_in_db = await self.__invoice_service.search_by_integration(
            integration_id=mp_sub.id,
            integration_type="mercado-pago"
        )
        return invoice_in_db

    async def update_subscription_payment(self, authorized_payment_id: str, data: dict) -> InvoiceInDB:
        authorized_payment = self.__mp_integration.get_authorized_payments(authorized_payment_id=authorized_payment_id)

        _logger.info(f"Authorized payment {authorized_payment['payment']['status']}")

        invoice_in_db = await self.__invoice_service.search_by_integration(
            integration_id=authorized_payment["preference_id"],
            integration_type="mercado-pago"
        )

        return invoice_in_db

    async def update_payment(self, payment_id: str) -> InvoiceInDB:
        payment_data = self.__mp_integration.get_payment(payment_id)
        payment_status = payment_data.get("status")

        status_map = {
            "approved": InvoiceStatus.PAID,
            "pending": InvoiceStatus.PENDING,
            "rejected": InvoiceStatus.REJECTED,
            "cancelled": InvoiceStatus.CANCELLED
        }

        internal_status = status_map.get(payment_status, InvoiceStatus.CANCELLED)
        integration_id = payment_data["external_reference"]

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

    async def get_subscription(self, organization_id: str) -> MPPreferenceModel:
        invoice_in_db = await self.__get_active_invoice(organization_id=organization_id)

        if invoice_in_db:
            mp_sub = self.__mp_integration.get_preference(preference_id=invoice_in_db.integration_id)
            return mp_sub

    async def unsubscribe(self, organization_id: str) -> MPPreferenceModel:
        invoice_in_db = await self.__get_active_invoice(organization_id=organization_id)

        if invoice_in_db:
            mp_sub = self.__mp_integration.cancel_subscription(preapproval_id=invoice_in_db.integration_id)
            return mp_sub

    async def __create_or_update_organization_plan(
            self,
            subscription: RequestSubscription,
            months_multiplier: int,
            start_date: datetime = None,
            end_date: datetime = None
        ) -> OrganizationPlanInDB:

        now = datetime.now() if not start_date else start_date
        today = datetime(year=now.year, month=now.month, day=now.day)
        sub_end = today + timedelta(days=30 * months_multiplier) if not end_date else end_date

        organization_plan_in_db = await self.__organization_plan_service.search_active_plan(
            organization_id=subscription.organization_id
        )

        if organization_plan_in_db and not start_date and not end_date:
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
