from typing import Dict, List
from app.crud.orders.schemas import OrderInDB, StoredProduct
from app.crud.products.repositories import ProductRepository


class OrderCalculator:

    def __init__(self, product_repository: ProductRepository):
        # The repository is kept for interface compatibility but is not used in
        # the calculations since product values are stored with their
        # additional costs already included.
        self.__product_repository = product_repository

    async def calculate(
        self,
        delivery_value: float,
        additional: float,
        discount: float,
        products: List[StoredProduct],
    ) -> float:
        total_amount = delivery_value + additional - discount

        for stored_product in products:
            total_amount += stored_product.unit_price * stored_product.quantity

        return round(total_amount, 2)

    async def get_totals_per_product(self, order: OrderInDB) -> Dict[str, dict]:
        products: Dict[str, dict] = {}

        for stored_product in order.products:
            if stored_product.product_id not in products:
                products[stored_product.product_id] = {
                    "product_id": stored_product.product_id,
                    "name": stored_product.name,
                    "total_cost": 0,
                    "total_amount": 0,
                    "quantity": 0,
                }

            product = products[stored_product.product_id]
            product["quantity"] += stored_product.quantity
            product["total_cost"] += stored_product.unit_cost * stored_product.quantity
            product["total_amount"] += stored_product.unit_price * stored_product.quantity

        return products
