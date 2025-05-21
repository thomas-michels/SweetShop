from typing import List
from app.crud.orders.schemas import StoredProduct
from app.crud.products.repositories import ProductRepository


class OrderCalculator:

    def __init__(self, product_repository: ProductRepository):
        self.__product_repository = product_repository

    async def calculate(
            self,
            delivery_value: float,
            additional: float,
            discount: float,
            products: List[StoredProduct]
        ) -> float:
        total_amount = delivery_value + additional - discount

        for stored_product in products:
            product_in_db = await self.__product_repository.select_by_id(
                id=stored_product.product_id
            )
            total_product = product_in_db.unit_price

            if stored_product.items:
                for item in stored_product.items:
                    total_product += item.unit_price * item.quantity

            total_amount += (total_product * stored_product.quantity)

        return round(total_amount, 2)
