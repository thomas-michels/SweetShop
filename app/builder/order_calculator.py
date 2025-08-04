from typing import Dict, List
from app.crud.orders.schemas import OrderInDB, StoredProduct
from app.crud.products.repositories import ProductRepository
from app.crud.products.schemas import ProductInDB


class OrderCalculator:

    def __init__(self, product_repository: ProductRepository):
        self.__product_repository = product_repository
        self.__products = {}

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

            for additional in stored_product.additionals:
                total_product += additional.unit_price * additional.quantity

            total_amount += (total_product * stored_product.quantity)

        return round(total_amount, 2)

    async def get_totals_per_product(self, order: OrderInDB) -> Dict[str, dict]:
        products = {}

        for stored_product in order.products:
            product_in_db = await self.__get_cached_product(product_id=stored_product.product_id)

            if not products.get(product_in_db.id):
                products[product_in_db.id] = {
                    "product_id": product_in_db.id,
                    "name": product_in_db.name,
                    "total_cost": 0,
                    "total_amount": 0,
                    "quantity": 0
                }

            product = products[product_in_db.id]

            cost = product_in_db.unit_cost
            price = product_in_db.unit_price

            for additional in stored_product.additionals:
                cost += additional.unit_cost * additional.quantity
                price += additional.unit_price * additional.quantity

            product["quantity"] += stored_product.quantity
            product["total_cost"] += (cost * stored_product.quantity)
            product["total_amount"] += (price * stored_product.quantity)

        return products

    async def __get_cached_product(self, product_id: str) -> ProductInDB:
        if product_id not in self.__products:
            product_in_db = await self.__product_repository.select_by_id(
                id=product_id
            )
            self.__products[product_id] = product_in_db
            return product_in_db

        else:
            return self.__products[product_id]
