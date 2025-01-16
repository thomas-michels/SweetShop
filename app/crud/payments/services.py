from typing import List

from app.crud.orders.repositories import OrderRepository

from .schemas import Payment, PaymentInDB, UpdatePayment
from .repositories import PaymentRepository



class PaymentServices:

    def __init__(
            self,
            payment_repository: PaymentRepository,
            order_repository: OrderRepository
        ) -> None:
        self.__payment_repository = payment_repository
        self.__order_repository = order_repository

    async def create(self, payment: Payment) -> PaymentInDB:
        await self.__order_repository.select_by_id(id=payment.order_id, fast_order=None)

        payment_in_db = await self.__payment_repository.create(payment=payment)
        return payment_in_db

    async def update(self, id: str, updated_payment: UpdatePayment) -> PaymentInDB:
        payment_in_db = await self.search_by_id(id=id)

        is_updated = payment_in_db.validate_updated_fields(update_payment=updated_payment)

        if is_updated:
            payment_in_db = await self.__payment_repository.update(payment=payment_in_db)

        return payment_in_db

    async def search_by_id(self, id: str) -> PaymentInDB:
        payment_in_db = await self.__payment_repository.select_by_id(id=id)
        return payment_in_db

    async def search_all(self, order_id: str) -> List[PaymentInDB]:
        payments = await self.__payment_repository.select_all(order_id=order_id)
        return payments

    async def delete_by_id(self, id: str) -> PaymentInDB:
        payment_in_db = await self.search_by_id(id=id)

        payment_in_db = await self.__payment_repository.delete_by_id(id=id)
        return payment_in_db
