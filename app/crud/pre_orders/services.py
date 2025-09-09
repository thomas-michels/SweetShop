from typing import List

from typing import TYPE_CHECKING
from app.crud.messages.schemas import Message, MessageType, Origin
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.customers.schemas import Customer
from app.crud.orders.schemas import (
    RequestOrder,
    RequestedProduct,
    RequestedAdditionalItem,
    Delivery,
    OrderInDB,
)
from app.crud.orders.services import OrderServices

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
        self.__organization_repository = organization_repository

        self.__message_services = message_services

    async def update_status(self, pre_order_id: str, new_status: PreOrderStatus, order_id: str | None = None, expand: List[str] = []) -> PreOrderInDB:
        pre_order_in_db = await self.__pre_order_repository.update_status(
            pre_order_id=pre_order_id,
            new_status=new_status,
            order_id=order_id,
        )

        await self.send_client_message(
            pre_order=pre_order_in_db
        )

        return pre_order_in_db

    async def reject_pre_order(self, pre_order_id: str) -> PreOrderInDB:
        return await self.update_status(
            pre_order_id=pre_order_id,
            new_status=PreOrderStatus.REJECTED,
        )

    async def accept_pre_order(
        self,
        pre_order_id: str,
        order_services: OrderServices,
    ) -> OrderInDB:
        pre_order = await self.search_by_id(id=pre_order_id)

        customer_in_db = await self.__customer_repository.select_by_phone(
            international_code=pre_order.customer.international_code,
            ddd=pre_order.customer.ddd,
            phone_number=pre_order.customer.phone_number,
            raise_404=False,
        )

        address = pre_order.delivery.address

        if customer_in_db is None:
            addresses = [address] if address else []
            customer = Customer(
                name=pre_order.customer.name,
                international_code=pre_order.customer.international_code,
                ddd=pre_order.customer.ddd,
                phone_number=pre_order.customer.phone_number,
                addresses=addresses,
                tags=[],
            )
            customer_in_db = await self.__customer_repository.create(customer=customer)

        else:
            if address and not any(
                addr.zip_code == address.zip_code for addr in customer_in_db.addresses
            ):
                customer_in_db.addresses.append(address)
                await self.__customer_repository.update(customer=customer_in_db)

        pre_order.customer.customer_id = customer_in_db.id

        requested_products: List[RequestedProduct] = []

        for product in pre_order.products:
            requested_products.append(
                RequestedProduct(
                    product_id=product.product_id,
                    quantity=product.quantity,
                    additionals=[
                        RequestedAdditionalItem(
                            item_id=add.item_id,
                            quantity=add.quantity,
                        )
                        for add in product.additionals
                    ],
                )
            )

        for offer in pre_order.offers:
            for item in offer.items:
                requested_products.append(
                    RequestedProduct(
                        product_id=item.item_id,
                        quantity=item.quantity * offer.quantity,
                        additionals=[
                            RequestedAdditionalItem(
                                item_id=add.item_id,
                                quantity=add.quantity,
                            )
                            for add in item.additionals
                        ],
                    )
                )

        delivery = Delivery(**pre_order.delivery.model_dump())
        now = UTCDateTime.now()
        request_order = RequestOrder(
            customer_id=pre_order.customer.customer_id,
            products=requested_products,
            delivery=delivery,
            preparation_date=now,
            order_date=now,
            description=pre_order.observation,
        )

        order_in_db = await order_services.create(order=request_order)
        await self.update_status(
            pre_order_id=pre_order_id,
            new_status=PreOrderStatus.ACCEPTED,
            order_id=order_in_db.id,
        )

        return order_in_db

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
