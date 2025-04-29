from typing import List

from app.crud.customers.repositories import CustomerRepository

from .repositories import PreOrderRepository
from .schemas import PreOrderInDB, PreOrderStatus


class PreOrderServices:

    def __init__(
        self,
        pre_order_repository: PreOrderRepository,
        customer_repository: CustomerRepository,
    ) -> None:
        self.__pre_order_repository = pre_order_repository
        self.__customer_repository = customer_repository

    async def update_status(self, pre_order_id: str, new_status: PreOrderStatus) -> PreOrderInDB:
        pre_order_in_db = await self.__pre_order_repository.update_status(
            pre_order_id=pre_order_id,
            new_status=new_status
        )

        return pre_order_in_db

    async def search_by_id(self, id: str) -> PreOrderInDB:
        pre_order_in_db = await self.__pre_order_repository.select_by_id(id=id)

        if pre_order_in_db:
            customer_in_db = await self.__customer_repository.select_by_phone(
                ddd=pre_order_in_db.customer.ddd,
                phone_number=pre_order_in_db.customer.phone_number,
                raise_404=False
            )

            if customer_in_db:
                pre_order_in_db.customer.customer_id = customer_in_db.id

        return pre_order_in_db

    async def search_all(self, status: PreOrderStatus = None) -> List[PreOrderInDB]:
        pre_orders = await self.__pre_order_repository.select_all(status=status)

        for pre_order_in_db in pre_orders:
            if pre_order_in_db:
                customer_in_db = await self.__customer_repository.select_by_phone(
                    ddd=pre_order_in_db.customer.ddd,
                    phone_number=pre_order_in_db.customer.phone_number,
                    raise_404=False
                )

                if customer_in_db:
                    pre_order_in_db.customer.customer_id = customer_in_db.id

        return pre_orders

    async def delete_by_id(self, id: str) -> PreOrderInDB:
        pre_order_in_db = await self.__pre_order_repository.delete_by_id(id=id)
        return pre_order_in_db
