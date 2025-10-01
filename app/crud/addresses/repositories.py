from typing import List

from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository
from app.core.utils.utc_datetime import UTCDateTime

from .models import AddressModel
from .schemas import AddressCreate, AddressInDB, AddressUpdate

_logger = get_logger(__name__)


class AddressRepository(Repository):
    def __init__(self) -> None:
        super().__init__()

    async def create(self, address: AddressCreate) -> AddressInDB:
        try:
            address_model = AddressModel(
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
                **address.model_dump(),
            )
            address_model.save()
            _logger.info(f"Address with CEP {address.zip_code} saved")
            return AddressInDB.model_validate(address_model)

        except Exception as error:
            _logger.error(f"Error on create_address: {str(error)}")
            raise UnprocessableEntity(message="Erro ao criar um novo endereço")

    async def select_by_zip_code(
        self, zip_code: str, raise_404: bool = True
    ) -> AddressInDB:
        try:
            zip_code = "".join(filter(str.isdigit, zip_code))

            address_model: AddressModel = AddressModel.objects(
                zip_code=zip_code,
                is_active=True,
            ).first()

            if address_model:
                return AddressInDB.model_validate(address_model)

            if raise_404:
                raise NotFoundError(message=f"CEP {zip_code} não encontrado")

            return None
        except Exception as error:
            _logger.error(f"Error on select_by_cep: {str(error)}")
            if raise_404:
                raise NotFoundError(message=f"Address with CEP {zip_code} not found")
            return None

    async def select_all(self) -> List[AddressInDB]:
        try:
            addresses = []

            objects = AddressModel.objects(
                is_active=True,
            ).order_by("zip_code")

            for address_model in objects:
                addresses.append(AddressInDB.model_validate(address_model))
            return addresses

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message="Addresses not found")

    async def update(self, id: str, address: AddressUpdate) -> AddressInDB:
        address_model: AddressModel | None = AddressModel.objects(
            id=id,
            is_active=True,
        ).first()

        if not address_model:
            raise NotFoundError(message=f"Address #{id} not found")

        try:
            address_model.update(**address.model_dump(exclude_none=True))
            address_model.reload()

            return AddressInDB.model_validate(address_model)

        except Exception as error:
            _logger.error(f"Error on update: {str(error)}")
            raise UnprocessableEntity(message="Erro ao atualizar endereco")

    async def delete_by_id(self, id: str) -> AddressInDB:
        try:
            address_model: AddressModel = AddressModel.objects(
                id=id,
                is_active=True,
            ).first()

            if address_model:
                address_model.delete()
                return AddressInDB.model_validate(address_model)

            raise NotFoundError(message=f"Address #{id} not found")

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Address #{id} not found")
