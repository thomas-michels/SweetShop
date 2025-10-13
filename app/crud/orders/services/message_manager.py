"""Concrete observer responsible for customer notifications."""
from __future__ import annotations

from typing import Dict, Optional

from app.crud.customers.repositories import CustomerRepository
from app.crud.customers.schemas import CustomerInDB
from app.crud.messages.schemas import Message, MessageType, Origin
from app.crud.messages.services import MessageServices
from app.crud.organizations.repositories import OrganizationRepository
from app.crud.orders.schemas import OrderStatus

from ..domain.events import OrderEvent
from ..domain.observers import OrderObserver

if False:  # pragma: no cover
    from ..domain.order import Order


class OrderMessageManager(OrderObserver):
    """Observer that sends WhatsApp notifications on status changes."""

    def __init__(
        self,
        *,
        message_services: MessageServices,
        customer_repository: CustomerRepository,
        organization_repository: OrganizationRepository,
        customer_cache: Optional[Dict[str, CustomerInDB]] = None,
    ) -> None:
        self.__message_services = message_services
        self.__customer_repository = customer_repository
        self.__organization_repository = organization_repository
        self.__customer_cache = customer_cache if customer_cache is not None else {}

    async def update(
        self,
        order: "Order",
        event: OrderEvent,
        **context: object,
    ) -> None:
        if event != OrderEvent.STATUS_CHANGED:
            return

        previous_status = context.get("old_status")
        if isinstance(previous_status, str):
            previous_status = OrderStatus(previous_status)
        await self.send_status_update(order=order, previous_status=previous_status)

    async def send_status_update(
        self,
        *,
        order: "Order",
        previous_status: Optional[OrderStatus],
    ) -> None:
        current_status = order.status.current_status

        if previous_status is not None and current_status == previous_status:
            return

        if current_status not in (
            OrderStatus.READY_FOR_DELIVERY,
            OrderStatus.DONE,
        ):
            return

        if not order.customer_id:
            return

        customer = self.__customer_cache.get(order.customer_id)

        if customer is None:
            customer = await self.__customer_repository.select_by_id(
                id=order.customer_id,
                raise_404=False,
            )

            if customer:
                self.__customer_cache[order.customer_id] = customer

        if not customer:
            return

        if not (customer.international_code and customer.ddd and customer.phone_number):
            return

        organization = await self.__organization_repository.select_by_id(
            id=order.organization_id
        )

        if not getattr(organization, "enable_order_notifications", False):
            return

        if current_status == OrderStatus.READY_FOR_DELIVERY:
            title = "*Seu pedido saiu para entrega!*"
            body = "Informamos que seu pedido saiu para entrega e chegará em breve!"
        else:
            title = "*Pedido finalizado!*"
            body = (
                "Informamos que seu pedido foi finalizado. Esperamos que tenha gostado!"
            )

        text_message = (
            f"{title}\n\n"
            f"Olá {customer.name.title()},\n\n"
            f"{body}\n\n"
            f"Em caso de dúvidas o número de contato do estabelecimento para contato é "
            f"+{organization.international_code} {organization.ddd} {organization.phone_number}\n\n"
            "_Está é uma mensagem automática gerada pela PedidoZ, por favor não responda!_"
        )

        message = Message(
            international_code=customer.international_code,
            ddd=customer.ddd,
            phone_number=customer.phone_number,
            message_type=MessageType.INFORMATION,
            origin=Origin.ORDERS,
            message=text_message,
        )

        await self.__message_services.create(message=message)
