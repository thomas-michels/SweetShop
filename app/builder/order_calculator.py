from typing import Dict, List
from app.crud.orders.schemas import OrderInDB, StoredProduct
from app.crud.products.repositories import ProductRepository


class OrderCalculator:

    def __init__(self, product_repository: ProductRepository):
        # The repository is kept for interface compatibility but is not used in
        # the calculations since all required values are already available in
        # the provided products.
        self.__product_repository = product_repository

    async def calculate(
        self,
        delivery_value: float,
        additional: float,
        discount: float,
        products: List[StoredProduct],
    ) -> float:
        """Calculate the total order amount.

        The calculation follows the business rules:

        1. sum product prices
        2. add prices of selected additional items
        3. include any order level additional charges
        4. subtract the discount (without affecting the delivery fee)
        5. add the delivery value

        The returned amount does **not** include tax, which must be applied
        separately by the service layer.
        """

        subtotal = additional

        for stored_product in products:
            subtotal += stored_product.unit_price * stored_product.quantity

            for additional_item in stored_product.additionals:
                subtotal += (
                    additional_item.unit_price
                    * additional_item.quantity
                    * stored_product.quantity
                )

        subtotal = max(subtotal - discount, 0)
        total_amount = subtotal + delivery_value

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

            for additional_item in stored_product.additionals:
                product["total_cost"] += (
                    additional_item.unit_cost
                    * additional_item.consumption_factor
                    * additional_item.quantity
                    * stored_product.quantity
                )
                product["total_amount"] += (
                    additional_item.unit_price
                    * additional_item.quantity
                    * stored_product.quantity
                )

        return products
