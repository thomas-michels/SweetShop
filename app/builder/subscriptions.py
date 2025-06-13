from datetime import timedelta
from typing import List
from uuid import uuid4

from app.api.dependencies.email_sender import send_email
from app.api.dependencies.mercado_pago_integration import MercadoPagoIntegration
from app.api.exceptions.authentication_exceptions import BadRequestException
from app.api.shared_schemas.mercado_pago import MPPreferenceModel
from app.api.shared_schemas.subscription import (
    RequestSubscription,
    ResponseSubscription,
)
from app.core.configs import get_logger
from app.core.utils.get_start_and_end_day_of_month import get_start_and_end_day_of_month
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.coupons.services import CouponServices
from app.crud.invoices.schemas import Invoice, InvoiceInDB, InvoiceStatus, UpdateInvoice
from app.crud.invoices.services import InvoiceServices
from app.crud.organization_plans.schemas import OrganizationPlan
from app.crud.organization_plans.services import OrganizationPlanServices
from app.crud.organizations.services import OrganizationServices
from app.crud.plans.services import PlanServices
from app.crud.shared_schemas.roles import RoleEnum
from app.crud.users.schemas import UserInDB

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

    async def subscribe(
        self, subscription: RequestSubscription, user: UserInDB
    ) -> ResponseSubscription:
        """Cria uma nova assinatura para uma organização sem plano ativo, permitindo cupons."""
        # Busca o plano solicitado
        plan_in_db = await self.__plan_service.search_by_id(id=subscription.plan_id)
        months_multiplier = subscription.get_sub_months()
        subscription_price = round(plan_in_db.price * months_multiplier, 2)

        # Verifica se já existe um plano ativo
        active_plan = await self.__organization_plan_service.search_active_plan(
            organization_id=subscription.organization_id
        )
        if active_plan:
            raise BadRequestException(
                "Organização já possui um plano ativo. Use 'alterar plano' para atualizar."
            )

        # Cria um novo plano começando hoje
        today = UTCDateTime.now().date()
        start_date = UTCDateTime.combine(today, UTCDateTime.min.time())  # 00:00:00 de hoje
        end_date = start_date + timedelta(days=30 * months_multiplier)
        new_plan = OrganizationPlan(
            plan_id=subscription.plan_id,
            allow_additional=subscription.allow_additional,
            start_date=start_date,
            end_date=end_date,
        )
        new_plan_in_db = await self.__organization_plan_service.create(
            organization_plan=new_plan, organization_id=subscription.organization_id
        )

        # Aplica desconto de cupom, se fornecido
        discount = 0
        observation = {}
        if subscription.coupon_id:
            coupon_in_db = await self.__coupon_service.search_by_id(
                id=subscription.coupon_id
            )
            coupon_in_db = await self.__coupon_service.update_usage(
                coupon_id=coupon_in_db.id, quantity=1
            )
            discount = coupon_in_db.calculate_discount(price=subscription_price)
            observation["discount"] = discount
            observation["coupon_id"] = subscription.coupon_id
            _logger.info(
                f"Desconto de R${discount} aplicado usando cupom {subscription.coupon_id}"
            )

        # Gera a preferência de pagamento e a fatura
        organization_in_db = await self.__organization_service.search_by_id(
            id=subscription.organization_id
        )
        user_info = {"email": organization_in_db.email or user.email, "name": user.name}
        label = subscription.get_label()
        invoice_in_db, init_point, external_reference = (
            await self._create_invoice_and_preference(
                plan_name=plan_in_db.name,
                subscription_price=subscription_price,
                discount=discount,
                user_info=user_info,
                label=label,
                organization_plan_id=new_plan_in_db.id,
                organization_id=subscription.organization_id,
                observation=observation,
            )
        )

        return ResponseSubscription(
            invoice_id=invoice_in_db.id,
            integration_id=external_reference,
            init_point=init_point,
            email=user_info["email"],
        )

    async def recreate_subscription(
        self, subscription: RequestSubscription, user: UserInDB
    ) -> ResponseSubscription:
        # Busca o plano solicitado
        plan_in_db = await self.__plan_service.search_by_id(id=subscription.plan_id)

        months_multiplier = subscription.get_sub_months()
        subscription_price = round(plan_in_db.price * months_multiplier, 2)

        today = UTCDateTime.now().date()
        start_date = UTCDateTime.combine(today, UTCDateTime.min.time())
        end_of_the_today = UTCDateTime.combine(today, UTCDateTime.max.time())

        end_date = start_date + timedelta(days=30 * months_multiplier)

        # Busca o plano atual da organização
        organization_plans = (
            await self.__organization_plan_service.check_if_period_is_available(
                organization_id=subscription.organization_id,
                start_date=start_date,
                end_date=end_of_the_today,
            )
        )

        if not organization_plans:
            raise BadRequestException("Organização não possui um plano para atualizar")

        # Verifica se o plano está pago
        current_organization_plan = organization_plans[0]

        invoices = await self.__invoice_service.search_by_organization_plan_id(
            organization_plan_id=current_organization_plan.id
        )

        paid_invoice = next(
            (invoice for invoice in invoices if invoice.status == InvoiceStatus.PAID),
            None,
        )

        await self.__cancel_pending_payments(
            organization_plan_id=current_organization_plan.id
        )

        credits = 0

        if paid_invoice:
            credits = self._calculate_remaining_credits(
                organization_plan=current_organization_plan,
                amount_paid=paid_invoice.amount_paid,
            )
            _logger.info(
                f"R${credits} de crédito gerados para o novo plano - organização {subscription.organization_id}"
            )

        today = UTCDateTime.now().date()
        start_date = UTCDateTime.combine(today, UTCDateTime.min.time())
        end_date = start_date + timedelta(days=30 * months_multiplier)

        new_plan = OrganizationPlan(
            plan_id=subscription.plan_id,
            allow_additional=subscription.allow_additional,
            start_date=start_date,
            end_date=end_date,
        )

        new_plan_in_db = await self.__organization_plan_service.create(
            organization_plan=new_plan, organization_id=subscription.organization_id
        )

        discount = credits
        observation = {"credits": credits} if credits > 0 else {}

        # Gera a preferência de pagamento e a fatura
        organization_in_db = await self.__organization_service.search_by_id(
            id=subscription.organization_id
        )

        user_info = {"email": organization_in_db.email or user.email, "name": user.name}

        label = subscription.get_label()

        invoice_in_db, init_point, external_reference = (
            await self._create_invoice_and_preference(
                plan_name=plan_in_db.name,
                subscription_price=subscription_price,
                discount=discount,
                user_info=user_info,
                label=label,
                organization_plan_id=new_plan_in_db.id,
                organization_id=subscription.organization_id,
                observation=observation,
            )
        )

        return ResponseSubscription(
            invoice_id=invoice_in_db.id,
            integration_id=external_reference,
            init_point=init_point,
            email=user_info["email"],
        )

    async def _create_invoice_and_preference(
        self,
        plan_name: str,
        subscription_price: float,
        discount: float,
        user_info: dict,
        label: str,
        organization_plan_id: str,
        organization_id: str,
        observation: dict,
    ) -> tuple[InvoiceInDB, str, str]:
        """Cria uma preferência de pagamento e uma fatura para a assinatura."""
        if subscription_price > 0:
            mp_preference = self.__mp_integration.create_preference(
                reason=f"pedidoZ - Assinatura {label} - {plan_name}",
                price_monthly=subscription_price,
                discount=discount,
                user_info=user_info,
            )
            external_reference = mp_preference.external_reference
            init_point = mp_preference.init_point
        else:
            external_reference = str(uuid4())
            init_point = "https://www.pedidoz.online/organizacoes"

        invoice = Invoice(
            organization_plan_id=organization_plan_id,
            integration_id=external_reference,
            integration_type="mercado-pago",
            amount=max(subscription_price - discount, 0),
            observation=observation,
        )
        if subscription_price == 0:
            invoice.status = InvoiceStatus.PAID
            invoice.amount_paid = 0

        invoice_in_db = await self.__invoice_service.create(invoice=invoice)

        return invoice_in_db, init_point, external_reference

    def _calculate_remaining_credits(
        self, organization_plan: OrganizationPlan, amount_paid: float
    ) -> float:
        """Calcula os créditos restantes com base no tempo restante do plano."""
        today = UTCDateTime.today()
        if not amount_paid:
            amount_paid = 0

        remaining_days = (organization_plan.end_date - today).days
        total_days = (organization_plan.end_date - organization_plan.start_date).days

        if total_days <= 0:
            return 0

        return round((remaining_days / total_days) * amount_paid, 2)

    def _adjust_end_date(self, current_end_date: UTCDateTime) -> UTCDateTime:
        """Ajusta a data de término do plano para o final do mês, se necessário."""
        end_of_month = self._get_end_of_current_month()
        return min(current_end_date, end_of_month)

    def _get_next_plan_dates(self, reference_date: UTCDateTime, months: int) -> tuple:
        """Obtém a data de início e fim do próximo plano."""
        next_month = reference_date.month % 12 + 1
        next_year = reference_date.year if next_month > 1 else reference_date.year + 1
        start_date, end_date = get_start_and_end_day_of_month(
            year=next_year, month=next_month
        )
        return start_date, end_date + timedelta(days=30 * months)

    def _get_end_of_current_month(self) -> UTCDateTime:
        """Retorna a data do último dia do mês atual."""
        today = UTCDateTime.today()
        next_month = today.replace(day=28) + timedelta(
            days=4
        )  # Garante que passamos para o próximo mês
        day = next_month - timedelta(days=next_month.day)
        return UTCDateTime(
            year=day.year, month=day.month, day=day.day, hour=23, minute=59, second=59
        )

    def _get_invoice(self, invoices: List[InvoiceInDB]) -> InvoiceInDB:
        for old_invoice_in_db in invoices:
            if old_invoice_in_db.status == InvoiceStatus.PAID:
                return old_invoice_in_db

    async def update_subscription(
        self, subscription_id: str, data: dict
    ) -> InvoiceInDB:
        mp_sub = self.__mp_integration.get_subscription(preapproval_id=subscription_id)
        invoice_in_db = await self.__invoice_service.search_by_integration(
            integration_id=mp_sub.id, integration_type="mercado-pago"
        )
        return invoice_in_db

    async def update_subscription_payment(
        self, authorized_payment_id: str, data: dict
    ) -> InvoiceInDB:
        authorized_payment = self.__mp_integration.get_authorized_payments(
            authorized_payment_id=authorized_payment_id
        )

        _logger.info(f"Authorized payment {authorized_payment['payment']['status']}")

        invoice_in_db = await self.__invoice_service.search_by_integration(
            integration_id=authorized_payment["preference_id"],
            integration_type="mercado-pago",
        )

        return invoice_in_db

    async def update_payment(self, payment_id: str) -> InvoiceInDB:
        payment_data = self.__mp_integration.get_payment(payment_id)

        if not payment_data:
            return

        payment_status = payment_data.get("status")

        status_map = {
            "approved": InvoiceStatus.PAID,
            "pending": InvoiceStatus.PENDING,
            "rejected": InvoiceStatus.REJECTED,
            "cancelled": InvoiceStatus.CANCELLED,
        }

        internal_status = status_map.get(payment_status, InvoiceStatus.CANCELLED)
        integration_id = payment_data["external_reference"]

        invoice_in_db = await self.__invoice_service.search_by_integration(
            integration_id=integration_id, integration_type="mercado-pago"
        )

        update_invoice = UpdateInvoice(status=internal_status)

        if internal_status == InvoiceStatus.PAID:
            update_invoice.paid_at = UTCDateTime.now()
            update_invoice.amount_paid = invoice_in_db.amount

            current_organization_plan = (
                await self.__organization_plan_service.search_by_id(
                    id=invoice_in_db.organization_plan_id
                )
            )

            user_in_db = await self.__get_organization_owner(
                organization_id=current_organization_plan.organization_id
            )

            # Cancel previous plans
            organization_plans = (
                await self.__organization_plan_service.check_if_period_is_available(
                    organization_id=current_organization_plan.organization_id,
                    start_date=current_organization_plan.start_date,
                    end_date=current_organization_plan.end_date,
                )
            )

            if organization_plans:
                yesterday = (UTCDateTime.now() - timedelta(days=1)).date()

                for organization_plan in organization_plans:
                    if organization_plan.id == current_organization_plan.id:
                        continue

                    if organization_plan.end_date < UTCDateTime.now():
                        continue

                    organization_plan.end_date = UTCDateTime.combine(
                        yesterday, UTCDateTime.max.time()
                    )

                    await self.__organization_plan_service.update(
                        id=organization_plan.id,
                        organization_id=organization_plan.organization_id,
                        updated_organization_plan=organization_plan,
                    )
                    _logger.info(
                        f"Plano atual finalizado em {organization_plan.end_date}"
                    )

            with open(
                "./templates/purchase-successed-email.html", mode="r", encoding="UTF-8"
            ) as file:
                message = file.read()
                message = message.replace("$USER_NAME$", user_in_db.name.title())

            send_email(
                email_to=[user_in_db.email],
                title=f"Seu pagamento foi confirmado!",
                message=message,
            )

        updated_invoice = await self.__invoice_service.update(
            id=invoice_in_db.id, updated_invoice=update_invoice
        )

        return updated_invoice

    async def get_subscription(self, organization_id: str) -> MPPreferenceModel:
        invoice_in_db = await self.__get_active_invoice(organization_id=organization_id)

        if invoice_in_db:
            mp_sub = self.__mp_integration.get_preference(
                preference_id=invoice_in_db.integration_id
            )
            return mp_sub

    async def unsubscribe(self, organization_id: str) -> MPPreferenceModel:
        invoice_in_db = await self.__get_active_invoice(organization_id=organization_id)

        if invoice_in_db:
            mp_sub = self.__mp_integration.cancel_subscription(
                preapproval_id=invoice_in_db.integration_id
            )
            return mp_sub

    async def __cancel_pending_payments(self, organization_plan_id: str) -> bool:
        invoices = await self.__invoice_service.search_by_organization_plan_id(
            organization_plan_id=organization_plan_id
        )

        for invoice_in_db in invoices:
            if invoice_in_db and invoice_in_db.status not in [
                InvoiceStatus.CANCELLED,
                InvoiceStatus.PAID,
            ]:
                invoice_in_db.status = InvoiceStatus.CANCELLED

                invoice_in_db = await self.__invoice_service.update(
                    id=invoice_in_db.id, updated_invoice=invoice_in_db
                )

        return True

    async def __get_active_invoice(self, organization_id: str) -> InvoiceInDB:
        organization_plan_in_db = (
            await self.__organization_plan_service.search_active_plan(
                organization_id=organization_id
            )
        )

        invoices = await self.__invoice_service.search_by_organization_plan_id(
            organization_plan_id=organization_plan_in_db.id
        )

        for invoice_in_db in invoices:
            if invoice_in_db.status == InvoiceStatus.PAID:
                return invoice_in_db

    async def __get_organization_owner(self, organization_id: str):
        organization_in_db = await self.__organization_service.search_by_id(
            id=organization_id, expand=["users"]
        )

        for user in organization_in_db.users:
            if user.role == RoleEnum.OWNER:
                return user
