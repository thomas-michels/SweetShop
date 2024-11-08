from typing import List
from .schemas import Customer, CustomerInDB, UpdateCustomer
from .repositories import CustomerRepository


class CustomerServices:

    def __init__(self, customer_repository: CustomerRepository) -> None:
        self.__repository = customer_repository

    async def create(self, customer: Customer) -> CustomerInDB:
        customer_in_db = await self.__repository.create(customer=customer)
        return customer_in_db

    async def update(self, id: str, updated_customer: UpdateCustomer) -> CustomerInDB:
        customer_in_db = await self.search_by_id(id=id)

        is_updated = customer_in_db.validate_updated_fields(update_customer=updated_customer)

        if is_updated:
            customer_in_db = await self.__repository.update(customer=customer_in_db)

        return customer_in_db

    async def search_by_id(self, id: str) -> CustomerInDB:
        customer_in_db = await self.__repository.select_by_id(id=id)
        return customer_in_db

    async def search_all(self, query: str) -> List[CustomerInDB]:
        customers = await self.__repository.select_all(query=query)
        return customers

    async def delete_by_id(self, id: str) -> CustomerInDB:
        customer_in_db = await self.__repository.delete_by_id(id=id)
        return customer_in_db
