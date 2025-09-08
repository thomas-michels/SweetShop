from typing import List

from typing import TYPE_CHECKING
from app.crud.messages.schemas import Message, MessageType, Origin
from app.api.exceptions.authentication_exceptions import BadRequestException

if TYPE_CHECKING:  # pragma: no cover
    from app.crud.messages.services import MessageServices
    from app.crud.customers.repositories import CustomerRepository
    from app.crud.offers.repositories import OfferRepository
    from app.crud.organizations.repositories import OrganizationRepository
    from app.crud.additional_items.repositories import AdditionalItemRepository
    from app.crud.product_additionals.repositories import ProductAdditionalRepository
    from .repositories import PreOrderRepository

from .schemas import (
    PreOrderInDB,
    PreOrderStatus,
    SelectedOffer,
    SelectedProduct,
)


class PreOrderServices:

    def __init__(
        self,
        pre_order_repository: 'PreOrderRepository',
        customer_repository: 'CustomerRepository',
        offer_repository: 'OfferRepository',
        organization_repository: 'OrganizationRepository',
        message_services: 'MessageServices',
        additional_item_repository: 'AdditionalItemRepository',
        product_additional_repository: 'ProductAdditionalRepository',
    ) -> None:
        self.__pre_order_repository = pre_order_repository
        self.__customer_repository = customer_repository
        self.__offer_repository = offer_repository
        self.__organization_repository = organization_repository

        self.__message_services = message_services
        self.__additional_item_repository = additional_item_repository
        self.__product_additional_repository = product_additional_repository

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

        return pre_order_in_db

    async def search_by_id(self, id: str, expand: List[str] = []) -> PreOrderInDB:
        pre_order_in_db = await self.__pre_order_repository.select_by_id(id=id)

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

        return pre_orders

    async def delete_by_id(self, id: str) -> PreOrderInDB:
        pre_order_in_db = await self.__pre_order_repository.delete_by_id(id=id)
        return pre_order_in_db

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

_Está é uma mensagem automática gerada pela PedidoZ, por favor não responda!_"""

        message = Message(
            international_code=pre_order.customer.international_code,
            ddd=pre_order.customer.ddd,
            phone_number=pre_order.customer.phone_number,
            message_type=MessageType.INFORMATION,
            origin=Origin.ORDERS,
            message=text_message
        )

        return await self.__message_services.create(message=message)
