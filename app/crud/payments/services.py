from typing import List

from app.api.exceptions.authentication_exceptions import BadRequestException
from app.core.exceptions.users import UnprocessableEntity
from app.crud.orders.repositories import OrderRepository
from app.crud.orders.schemas import OrderInDB
from app.crud.shared_schemas.payment import PaymentStatus

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
        order_in_db = await self.__order_repository.select_by_id(id=payment.order_id, fast_order=None)

        if order_in_db.payment_status == PaymentStatus.PAID:
            raise BadRequestException(detail="Order already paid!")

        payment_in_db = await self.__payment_repository.create(payment=payment)

        await self.update_payment_status(order_in_db=order_in_db)

        return payment_in_db

    async def update(self, id: str, updated_payment: UpdatePayment) -> PaymentInDB:
        payment_in_db = await self.search_by_id(id=id)

        is_updated = payment_in_db.validate_updated_fields(update_payment=updated_payment)

        if is_updated:
            payment_in_db = await self.__payment_repository.update(payment=payment_in_db)

        order_in_db = await self.__order_repository.select_by_id(
            id=payment_in_db.id,
            fast_order=None
        )

        await self.update_payment_status(order_in_db=order_in_db)

        return payment_in_db

    async def search_by_id(self, id: str) -> PaymentInDB:
        payment_in_db = await self.__payment_repository.select_by_id(id=id)
        return payment_in_db

    async def search_all(self, order_id: str) -> List[PaymentInDB]:
        payments = await self.__payment_repository.select_all(order_id=order_id)
        return payments

    async def delete_by_id(self, id: str) -> PaymentInDB:
        payment_in_db = await self.search_by_id(id=id)
        order_in_db = await self.__order_repository.select_by_id(
            id=payment_in_db.order_id,
            fast_order=None
        )

        payment_in_db = await self.__payment_repository.delete_by_id(id=id)

        await self.update_payment_status(order_in_db=order_in_db)

        return payment_in_db

    async def update_payment_status(self, order_in_db: OrderInDB) -> None:
        payments = await self.search_all(order_id=order_in_db.id)

        payment_status = self.__calculate_payment_status(
            total_amount=order_in_db.total_amount,
            payment_details=payments
        )

        if order_in_db.payment_status != payment_status:
            try:
                await self.__order_repository.update(
                    order_id=order_in_db.id,
                    order={"payment_status": payment_status}
                )

            except UnprocessableEntity:
                ...

    def __calculate_payment_status(self, total_amount: float, payment_details: List[Payment]) -> PaymentStatus:
        if payment_details:
            total_paid = 0

            for payment in payment_details:
                total_paid += payment.amount

            if round(total_amount, 2) <= round(total_paid, 2):
                return PaymentStatus.PAID

            else:
                return PaymentStatus.PARTIALLY_PAID

        return PaymentStatus.PENDING
