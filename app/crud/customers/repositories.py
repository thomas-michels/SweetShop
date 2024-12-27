from datetime import datetime
from typing import List
from mongoengine.errors import NotUniqueError
from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository

from .models import CustomerModel
from .schemas import Customer, CustomerInDB

_logger = get_logger(__name__)


class CustomerRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.__organization_id = organization_id

    async def create(self, customer: Customer) -> CustomerInDB:
        try:
            customer_model = CustomerModel(
                created_at=datetime.now(),
                updated_at=datetime.now(),
                organization_id=self.__organization_id,
                **customer.model_dump()
            )
            customer_model.name = customer_model.name.title()

            customer_model.save()

            return CustomerInDB.model_validate(customer_model)

        except NotUniqueError:
            _logger.warning(f"Customer {customer.name} is not unique")
            return await self.select_by_name(name=customer.name)

        except Exception as error:
            _logger.error(f"Error on create_customer: {str(error)}")
            raise UnprocessableEntity(message="Error on create new Customer")

    async def update(self, customer: CustomerInDB) -> CustomerInDB:
        try:
            customer_model: CustomerModel = CustomerModel.objects(
                id=customer.id,
                is_active=True,
                organization_id=self.__organization_id
            ).first()
            customer.name = customer.name.title()

            customer_model.update(**customer.model_dump())

            return await self.select_by_id(id=customer.id)

        except Exception as error:
            _logger.error(f"Error on update_customer: {str(error)}")
            raise UnprocessableEntity(message="Error on update Customer")

    async def select_by_id(self, id: str, raise_404: bool = True) -> CustomerInDB:
        try:
            customer_model: CustomerModel = CustomerModel.objects(
                id=id,
                is_active=True,
                organization_id=self.__organization_id
            ).first()

            return CustomerInDB.model_validate(customer_model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            if raise_404:
                raise NotFoundError(message=f"Customer #{id} not found")

    async def select_by_name(self, name: str) -> CustomerInDB:
        try:
            name = name.capitalize()
            customer_model: CustomerModel = CustomerModel.objects(
                name=name,
                is_active=True,
                organization_id=self.__organization_id
            ).first()

            return CustomerInDB.model_validate(customer_model)

        except Exception as error:
            _logger.error(f"Error on select_by_name: {str(error)}")
            raise NotFoundError(message=f"Customer with {name} not found")

    async def select_all(self, query: str) -> List[CustomerInDB]:
        try:
            customers = []

            if query:
                objects = CustomerModel.objects(
                    is_active=True,
                    name__iregex=query,
                    organization_id=self.__organization_id
                )

            else:
                objects = CustomerModel.objects(
                    is_active=True,
                    organization_id=self.__organization_id
                )

            for customer_model in objects.order_by("name"):
                customers.append(CustomerInDB.model_validate(customer_model))

            return customers

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"Customers not found")

    async def delete_by_id(self, id: str) -> CustomerInDB:
        try:
            customer_model: CustomerModel = CustomerModel.objects(
                id=id,
                is_active=True,
                organization_id=self.__organization_id
            ).first()
            customer_model.delete()

            return CustomerInDB.model_validate(customer_model)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Customer #{id} not found")
