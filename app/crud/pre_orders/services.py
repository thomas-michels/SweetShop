from typing import List

from app.crud.customers.repositories import CustomerRepository
from app.crud.offers.repositories import OfferRepository

from .repositories import PreOrderRepository
from .schemas import CompletePreOrder, PreOrderInDB, PreOrderStatus


class PreOrderServices:

    def __init__(
        self,
        pre_order_repository: PreOrderRepository,
        customer_repository: CustomerRepository,
        offer_repository: OfferRepository,
    ) -> None:
        self.__pre_order_repository = pre_order_repository
        self.__customer_repository = customer_repository
        self.__offer_repository = offer_repository
        self.__cache_customers = {}
        self.__cache_offers = {}

    async def update_status(self, pre_order_id: str, new_status: PreOrderStatus) -> PreOrderInDB:
        pre_order_in_db = await self.__pre_order_repository.update_status(
            pre_order_id=pre_order_id,
            new_status=new_status
        )

        return pre_order_in_db

    async def search_by_id(self, id: str, expand: List[str] = []) -> PreOrderInDB:
        pre_order_in_db = await self.__pre_order_repository.select_by_id(id=id)

        if pre_order_in_db:
            return await self.__build_pre_order(
                pre_order_in_db=pre_order_in_db,
                expand=expand
            )

        return pre_order_in_db

    async def search_all(self, status: PreOrderStatus = None, expand: List[str] = []) -> List[PreOrderInDB]:
        pre_orders = await self.__pre_order_repository.select_all(status=status)

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

        full_phone = f"{pre_order_in_db.customer.ddd}{pre_order_in_db.customer.phone_number}"

        if full_phone not in self.__cache_customers:
            customer_in_db = await self.__customer_repository.select_by_phone(
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
                    complete_offers.append(offer_in_db)

            complete_pre_order.offers = complete_offers

        return complete_pre_order
