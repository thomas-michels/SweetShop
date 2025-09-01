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

    async def __build_pre_order(self, pre_order_in_db: PreOrderInDB, expand: List[str] = []) -> PreOrderInDB:
        pre_order = PreOrderInDB.model_validate(pre_order_in_db)

        offers: List[SelectedOffer] = [
            item for item in pre_order.items if isinstance(item, SelectedOffer)
        ]
        products: List[SelectedProduct] = [
            item for item in pre_order.items if isinstance(item, SelectedProduct)
        ]

        await self.__validate_offers(offers)
        await self.__validate_products(products)

        full_phone = f"{pre_order.customer.international_code}{pre_order.customer.ddd}{pre_order.customer.phone_number}"

        if full_phone not in self.__cache_customers:
            customer_in_db = await self.__customer_repository.select_by_phone(
                international_code=pre_order.customer.international_code,
                ddd=pre_order.customer.ddd,
                phone_number=pre_order.customer.phone_number,
                raise_404=False
            )
            self.__cache_customers[full_phone] = customer_in_db

        else:
            customer_in_db = self.__cache_customers.get(full_phone)

        if customer_in_db:
            pre_order.customer.customer_id = customer_in_db.id

        if "offers" in expand:
            complete_offers = []

            for offer in offers:
                if offer.offer_id not in self.__cache_offers:
                    offer_in_db = await self.__offer_repository.select_by_id(
                        id=offer.offer_id, raise_404=False
                    )
                    self.__cache_offers[offer.offer_id] = offer_in_db

                else:
                    offer_in_db = self.__cache_offers.get(offer.offer_id)

                if offer_in_db:
                    offer_copy = offer_in_db.model_copy(deep=True)
                    offer_copy.quantity = offer.quantity
                    if offer.items:
                        offer_copy.items = offer.items
                    complete_offers.append(offer_copy)

            offers = complete_offers

        pre_order.items = [*products, *offers]

        return pre_order

    async def __validate_offers(self, offers: List[SelectedOffer]) -> List[SelectedOffer]:
        for offer in offers:
            if not offer.items:
                continue

            for item in offer.items:
                additionals_group = await self.__product_additional_repository.select_by_product_id(
                    product_id=item.item_id
                )

                group_map = {grp.id: grp for grp in additionals_group}
                group_counts = {grp.id: 0 for grp in additionals_group}

                if not item.additionals:
                    item.additionals = []

                for additional in item.additionals:
                    item_in_db = await self.__additional_item_repository.select_by_id(id=additional.item_id)

                    if (
                        item_in_db.additional_id not in group_map
                        or item_in_db.additional_id != additional.additional_id
                    ):
                        raise BadRequestException(
                            detail="Additional item not allowed for this product"
                        )

                    group_counts[item_in_db.additional_id] += additional.quantity
                    item.unit_price += item_in_db.unit_price * additional.quantity
                    item.unit_cost += item_in_db.unit_cost * additional.quantity

                for grp_id, grp in group_map.items():
                    count = group_counts.get(grp_id, 0)
                    if item.additionals and (count < grp.min_quantity or count > grp.max_quantity):
                        raise BadRequestException(
                            detail=f"Invalid quantity for additional group {grp.name}"
                        )

        return offers

    async def __validate_products(self, products: List[SelectedProduct]) -> List[SelectedProduct]:
        for product in products:
            additionals_group = await self.__product_additional_repository.select_by_product_id(
                product_id=product.product_id
            )

            group_map = {grp.id: grp for grp in additionals_group}
            group_counts = {grp.id: 0 for grp in additionals_group}

            for additional in product.additionals:
                item_in_db = await self.__additional_item_repository.select_by_id(id=additional.item_id)

                if (
                    item_in_db.additional_id not in group_map
                    or item_in_db.additional_id != additional.additional_id
                ):
                    raise BadRequestException(
                        detail="Additional item not allowed for this product"
                    )

                group_counts[item_in_db.additional_id] += additional.quantity
                product.unit_price += item_in_db.unit_price * additional.quantity
                product.unit_cost += item_in_db.unit_cost * additional.quantity

            for grp_id, grp in group_map.items():
                count = group_counts.get(grp_id, 0)
                if product.additionals and (count < grp.min_quantity or count > grp.max_quantity):
                    raise BadRequestException(
                        detail=f"Invalid quantity for additional group {grp.name}"
                    )

        return products

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
