from typing import List

from app.api.dependencies.get_plan_feature import get_plan_feature
from app.api.exceptions.authentication_exceptions import UnauthorizedException
from app.core.utils.features import Feature
from app.crud.tags.repositories import TagRepository

from .repositories import CustomerRepository
from .schemas import CompleteCustomerInDB, Customer, CustomerInDB, UpdateCustomer


class CustomerServices:

    def __init__(
        self,
        customer_repository: CustomerRepository,
        tag_repository: TagRepository,
    ) -> None:
        self.__repository = customer_repository
        self.__tag_repository = tag_repository
        self.__cache_tags = {}

    async def create(self, customer: Customer) -> CompleteCustomerInDB:
        plan_feature = await get_plan_feature(
            organization_id=self.__repository.organization_id,
            feature_name=Feature.MAX_CUSTOMERS,
        )

        quantity = await self.__repository.select_count()

        if not plan_feature or (
            plan_feature.value != "-" and (quantity + 1) >= int(plan_feature.value)
        ):
            raise UnauthorizedException(
                detail=f"Máximo de clientes atingido, Valor máximo: {plan_feature.value}"
            )

        for tag in customer.tags:
            await self.__tag_repository.select_by_id(id=tag)

        customer_in_db = await self.__repository.create(customer=customer)

        return await self.__build_complete_customer(customer_in_db=customer_in_db)

    async def update(
        self, id: str, updated_customer: UpdateCustomer
    ) -> CompleteCustomerInDB:
        customer_in_db = await self.search_by_id(id=id)

        is_updated = customer_in_db.validate_updated_fields(
            update_customer=updated_customer
        )

        if updated_customer.tags is not None:
            temp_tags = updated_customer.tags
            for tag in temp_tags:
                if not await self.__tag_repository.select_by_id(
                    id=tag, raise_404=False
                ):
                    updated_customer.tags.remove(tag)

        if is_updated:
            customer_in_db = await self.__repository.update(customer=customer_in_db)

        return await self.__build_complete_customer(customer_in_db=customer_in_db)

    async def search_count(self, query: str = None, tags: List[str] = []) -> int:
        return await self.__repository.select_count(
            query=query,
            tags=tags
        )

    async def search_by_id(
        self, id: str, expand: List[str] = []
    ) -> CompleteCustomerInDB:
        customer_in_db = await self.__repository.select_by_id(id=id)
        return await self.__build_complete_customer(
            customer_in_db=customer_in_db, expand=expand
        )

    async def search_all(
        self,
        query: str,
        tags: List[str] = [],
        expand: List[str] = [],
        page: int = None,
        page_size: int = None
    ) -> List[CompleteCustomerInDB]:
        customers = await self.__repository.select_all(
            query=query,
            tags=tags,
            page=page,
            page_size=page_size
        )
        all_customers = []

        for customer in customers:
            all_customers.append(
                await self.__build_complete_customer(
                    customer_in_db=customer, expand=expand
                )
            )

        return all_customers

    async def delete_by_id(self, id: str) -> CompleteCustomerInDB:
        customer_in_db = await self.__repository.delete_by_id(id=id)
        return await self.__build_complete_customer(customer_in_db=customer_in_db)

    async def __build_complete_customer(
        self, customer_in_db: CustomerInDB, expand: List[str] = []
    ) -> CompleteCustomerInDB:
        complete_customer = CompleteCustomerInDB.model_validate(customer_in_db)

        if "tags" in expand:
            complete_customer.tags = []

            for tag in customer_in_db.tags:
                if tag not in self.__cache_tags:
                    tag_in_db = await self.__tag_repository.select_by_id(
                        id=tag, raise_404=False
                    )
                    self.__cache_tags[tag] = tag_in_db

                else:
                    tag_in_db = self.__cache_tags[tag]

                if tag_in_db:
                    complete_customer.tags.append(tag_in_db)

        return complete_customer
