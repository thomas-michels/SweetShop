from typing import List
from mongoengine.errors import NotUniqueError
from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository
from app.core.utils.utc_datetime import UTCDateTime

from .models import CustomerModel
from .schemas import Customer, CustomerInDB

_logger = get_logger(__name__)


class CustomerRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.organization_id = organization_id

    async def create(self, customer: Customer) -> CustomerInDB:
        if customer.international_code and customer.ddd and customer.phone_number:
            if await self.select_by_phone(
                international_code=customer.international_code,
                ddd=customer.ddd,
                phone_number=customer.phone_number,
                raise_404=False
            ):
                raise UnprocessableEntity(
                    message="Um cliente com esse telefone já foi cadastrado"
                )

        if customer.email:
            if await self.select_by_email(
                email=customer.email,
                raise_404=False
            ):
                raise UnprocessableEntity(
                    message="Um cliente com esse email já foi cadastrado"
                )

        try:
            customer_model = CustomerModel(
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
                organization_id=self.organization_id,
                **customer.model_dump(),
            )
            customer_model.name = customer_model.name.strip().title()

            customer_model.save()

            return CustomerInDB.model_validate(customer_model)

        except NotUniqueError:
            _logger.warning(f"Customer {customer.name} is not unique")
            return await self.select_by_name(name=customer.name)

        except Exception as error:
            _logger.error(f"Error on create_customer: {str(error)}")
            raise UnprocessableEntity(message="Erro ao criar cliente")

    async def update(self, customer: CustomerInDB) -> CustomerInDB:
        if customer.international_code and customer.ddd and customer.phone_number:
            customer_with_same_phone = await self.select_by_phone(
                international_code=customer.international_code,
                ddd=customer.ddd,
                phone_number=customer.phone_number,
                raise_404=False
            )
            if customer_with_same_phone and customer_with_same_phone.id != customer.id:
                raise UnprocessableEntity(
                    message="Um cliente com esse telefone já foi cadastrado"
                )

        if customer.email:
            customer_with_same_email = await self.select_by_email(
                email=customer.email,
                raise_404=False
            )
            if customer_with_same_email and customer_with_same_email.id != customer.id:
                raise UnprocessableEntity(
                    message="Um cliente com esse email já foi cadastrado"
                )

        try:
            customer_model: CustomerModel = CustomerModel.objects(
                id=customer.id, is_active=True, organization_id=self.organization_id
            ).first()
            customer.name = customer.name.strip().title()

            customer_model.update(**customer.model_dump())

            return await self.select_by_id(id=customer.id)

        except Exception as error:
            _logger.error(f"Error on update_customer: {str(error)}")
            raise UnprocessableEntity(message="Erro ao atualizar cliente")

    async def select_count(self, query: str = None, tags: List[str] = []) -> int:
        try:
            objects = CustomerModel.objects(
                is_active=True,
                organization_id=self.organization_id,
            )

            if query:
                objects = objects.filter(name__iregex=query)

            if tags:
                objects = objects.filter(tags__in=tags)

            return max(objects.count(), 0)

        except Exception as error:
            _logger.error(f"Error on select_count: {str(error)}")
            return 0

    async def select_by_id(self, id: str, raise_404: bool = True) -> CustomerInDB:
        try:
            customer_model: CustomerModel = CustomerModel.objects(
                id=id, is_active=True, organization_id=self.organization_id
            ).first()

            if customer_model:
                return CustomerInDB.model_validate(customer_model)

            elif raise_404:
                raise NotFoundError(
                    message=f"Cliente com o ID #{id} não foi encontrado"
                )

        except Exception as error:
            if raise_404:
                raise NotFoundError(
                    message=f"Cliente com o ID #{id} não foi encontrado"
                )

            _logger.error(f"Error on select_by_id: {str(error)}")

    async def select_by_phone(
        self,
        ddd: str,
        phone_number: str,
        international_code: str = "55",
        raise_404: bool = True
    ) -> CustomerInDB:
        try:
            customer_model: CustomerModel = CustomerModel.objects(
                international_code=international_code,
                ddd=ddd,
                phone_number=phone_number,
                is_active=True,
                organization_id=self.organization_id,
            ).first()

            if customer_model:
                return CustomerInDB.model_validate(customer_model)

            elif raise_404:
                raise NotFoundError(
                    message=f"Cliente com o telefone {ddd} {phone_number} não foi encontrado"
                )

        except Exception as error:
            if raise_404:
                raise NotFoundError(
                    message=f"Cliente com o telefone {ddd} {phone_number} não foi encontrado"
                )

            _logger.error(f"Error on select_by_phone: {str(error)}")

    async def select_by_email(
        self,
        email: str,
        raise_404: bool = True
    ) -> CustomerInDB:
        try:
            customer_model: CustomerModel = CustomerModel.objects(
                email=email,
                is_active=True,
                organization_id=self.organization_id,
            ).first()

            if customer_model:
                return CustomerInDB.model_validate(customer_model)

            elif raise_404:
                raise NotFoundError(
                    message=f"Cliente com o email {email} não foi encontrado"
                )

        except Exception as error:
            if raise_404:
                raise NotFoundError(
                    message=f"Cliente com o email {email} não foi encontrado"
                )

            _logger.error(f"Error on select_by_email: {str(error)}")

    async def select_by_name(self, name: str) -> CustomerInDB:
        try:
            name = name.strip().title()

            customer_model: CustomerModel = CustomerModel.objects(
                name=name, is_active=True, organization_id=self.organization_id
            ).first()

            if customer_model:
                return CustomerInDB.model_validate(customer_model)

            raise NotFoundError(message=f"Cliente com o nome {name} não foi encontrado")

        except Exception as error:
            _logger.error(f"Error on select_by_name: {str(error)}")
            raise NotFoundError(message=f"Cliente com o nome {name} não foi encontrado")

    async def select_all(
        self, query: str, tags: List[str] = [], page: int = None, page_size: int = None
    ) -> List[CustomerInDB]:
        try:
            customers = []

            objects = CustomerModel.objects(
                is_active=True, organization_id=self.organization_id
            )

            if query:
                objects = objects.filter(name__iregex=query)

            if tags:
                objects = objects.filter(tags__in=tags)

            skip = (page - 1) * page_size
            objects = objects.order_by("name").skip(skip).limit(page_size)

            for customer_model in objects:
                customers.append(CustomerInDB.model_validate(customer_model))

            return customers

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"Clientes não foram encontrados")

    async def delete_by_id(self, id: str) -> CustomerInDB:
        try:
            customer_model: CustomerModel = CustomerModel.objects(
                id=id, is_active=True, organization_id=self.organization_id
            ).first()

            if customer_model:
                customer_model.delete()

                return CustomerInDB.model_validate(customer_model)

            raise NotFoundError(message=f"Cliente com o ID #{id} não foi encontrado")

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Cliente com o ID #{id} não foi encontrado")
