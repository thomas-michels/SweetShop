from __future__ import annotations

from typing import Dict, Optional

from app.crud.customers.repositories import CustomerRepository
from app.crud.customers.schemas import CustomerInDB
from app.crud.messages.schemas import Message, MessageType, Origin
from app.crud.messages.services import MessageServices
from app.crud.organizations.repositories import OrganizationRepository

from .schemas import OrderInDB, OrderStatus


class OrderMessageManager:
    def __init__(
        self,
        *,
        message_services: MessageServices,
        customer_repository: CustomerRepository,
        organization_repository: OrganizationRepository,
    ) -> None:
        self.__message_services = message_services
        self.__customer_repository = customer_repository
        self.__organization_repository = organization_repository

    async def send_status_update(
        self,
        *,
        order: OrderInDB,
        previous_status: Optional[OrderStatus],
        organization_id: str,
        customer_cache: Optional[Dict[str, CustomerInDB]] = None,
    ) -> None:
        if previous_status is not None and order.status == previous_status:
            return

        if order.status not in (
            OrderStatus.READY_FOR_DELIVERY,
            OrderStatus.DONE,
        ):
            return

        if not order.customer_id:
            return

        cache = customer_cache if customer_cache is not None else {}

        customer = cache.get(order.customer_id)

        if customer is None:
            customer = await self.__customer_repository.select_by_id(
                id=order.customer_id,
                raise_404=False,
            )

            if customer:
                cache[order.customer_id] = customer

        if not customer:
            return

        if not (customer.international_code and customer.ddd and customer.phone_number):
            return

        organization = await self.__organization_repository.select_by_id(
            id=organization_id
        )

        if not getattr(organization, "enable_order_notifications", False):
            return

        if order.status == OrderStatus.READY_FOR_DELIVERY:
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
