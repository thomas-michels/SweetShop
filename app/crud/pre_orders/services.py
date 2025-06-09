from typing import List

from app.crud.customers.repositories import CustomerRepository
from app.crud.messages.services import MessageServices
from app.crud.messages.schemas import Message, MessageType, Origin
from app.crud.offers.repositories import OfferRepository
from app.crud.organizations.repositories import OrganizationRepository

from .repositories import PreOrderRepository
from .schemas import CompletePreOrder, PreOrderInDB, PreOrderStatus


class PreOrderServices:

    def __init__(
        self,
        pre_order_repository: PreOrderRepository,
        customer_repository: CustomerRepository,
        offer_repository: OfferRepository,
        organization_repository: OrganizationRepository,
        message_services: MessageServices
    ) -> None:
        self.__pre_order_repository = pre_order_repository
        self.__customer_repository = customer_repository
        self.__offer_repository = offer_repository
        self.__organization_repository = organization_repository

        self.__message_services = message_services

        self.__cache_customers = {}
        self.__cache_offers = {}

    async def update_status(self, pre_order_id: str, new_status: PreOrderStatus, expand: List[str] = []) -> PreOrderInDB:
        pre_order_in_db = await self.__pre_order_repository.update_status(
            pre_order_id=pre_order_id,
            new_status=new_status
        )

        await self.send_client_message(
            pre_order=pre_order_in_db
        )

        return await self.__build_pre_order(
            pre_order_in_db=pre_order_in_db,
            expand=expand
        )

    async def search_by_id(self, id: str, expand: List[str] = []) -> PreOrderInDB:
        pre_order_in_db = await self.__pre_order_repository.select_by_id(id=id)

        if pre_order_in_db:
            return await self.__build_pre_order(
                pre_order_in_db=pre_order_in_db,
                expand=expand
            )

        return pre_order_in_db

    async def search_count(self, status: PreOrderStatus = None, code: str = None) -> int:
        return await self.__pre_order_repository.select_count(status=status, code=code)

    async def search_all(
            self,
            status: PreOrderStatus = None,
            code: str = None,
            expand: List[str] = [],
            page: int = None,
            page_size: int = None
        ) -> List[PreOrderInDB]:
        pre_orders = await self.__pre_order_repository.select_all(
            status=status,
            code=code,
            page=page,
            page_size=page_size
        )

        complete_pre_orders = []

        for pre_order_in_db in pre_orders:
            if pre_order_in_db:
                complete_pre_orders.append(
                    await self.__build_pre_order(
                        pre_order_in_db=pre_order_in_db,
                        expand=expand
                    )
                )

        return complete_pre_orders

    async def delete_by_id(self, id: str) -> PreOrderInDB:
        pre_order_in_db = await self.__pre_order_repository.delete_by_id(id=id)
        return pre_order_in_db

    async def __build_pre_order(self, pre_order_in_db: PreOrderInDB, expand: List[str] = []) -> CompletePreOrder:
        complete_pre_order = CompletePreOrder.model_validate(pre_order_in_db)

        full_phone = f"{pre_order_in_db.customer.international_code}{pre_order_in_db.customer.ddd}{pre_order_in_db.customer.phone_number}"

        if full_phone not in self.__cache_customers:
            customer_in_db = await self.__customer_repository.select_by_phone(
                international_code=pre_order_in_db.customer.international_code,
                ddd=pre_order_in_db.customer.ddd,
                phone_number=pre_order_in_db.customer.phone_number,
                raise_404=False
            )
            self.__cache_customers[full_phone] = customer_in_db

        else:
            customer_in_db = self.__cache_customers.get(full_phone)

        if customer_in_db:
            pre_order_in_db.customer.customer_id = customer_in_db.id

        if "offers" in expand:
            complete_offers = []

            for offer in complete_pre_order.offers:
                if offer.offer_id not in self.__cache_offers:
                    offer_in_db = await self.__offer_repository.select_by_id(id=offer.offer_id, raise_404=False)
                    self.__cache_offers[offer.offer_id] = offer_in_db

                else:
                    offer_in_db = self.__cache_offers.get(offer.offer_id)

                if offer_in_db:
                    offer_copy = offer_in_db.model_copy(deep=True)
                    offer_copy.quantity = offer.quantity
                    complete_offers.append(offer_copy)

            complete_pre_order.offers = complete_offers

        return complete_pre_order

    async def send_client_message(self, pre_order: PreOrderInDB) -> bool:
        if not (pre_order.customer.international_code and pre_order.customer.ddd and pre_order.customer.phone_number):
            return False

        organization = await self.__organization_repository.select_by_id(
            id=self.__pre_order_repository.organization_id
        )

        status = "ACEITO" if pre_order.status.startswith("A") else "RECUSADO"

        text_message = f"""*Seu pedido foi atualizado!*

Olá {pre_order.customer.name.title()},

Informamos que seu pedido foi *{status}*.
Aguarde o contato estabelecimento para maiores informações!

Em caso de dúvidas o número de contato do estabelecimento para contato é +{organization.international_code} {organization.ddd} {organization.phone_number}

_pedidoZ_"""

        message = Message(
            international_code=pre_order.customer.international_code,
            ddd=pre_order.customer.ddd,
            phone_number=pre_order.customer.phone_number,
            message_type=MessageType.INFORMATION,
            origin=Origin.ORDERS,
            message=text_message
        )

        return await self.__message_services.create(message=message)
