from typing import List

from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.utils.coordinator import Coordinator
from app.core.utils.get_address_by_zip_code import get_address_by_zip_code
from .schemas import AddressCreate, AddressInDB, AddressUpdate
from .repositories import AddressRepository


class AddressServices:
    def __init__(self, address_repository: AddressRepository) -> None:
        self.__address_repository = address_repository
        self.coordinator = Coordinator()

    async def create(self, address: AddressCreate) -> AddressInDB:
        try:
            address_in_db = await self.__address_repository.create(address=address)

            if not address_in_db.longitude:
                latitude, longitude = self.coordinator.get_coordinates(address=address_in_db)
                address_in_db.latitude = latitude
                address_in_db.longitude = longitude

                address_in_db = await self.__address_repository.update(
                    id=address_in_db.id,
                    address=AddressUpdate.model_validate(address_in_db)
                )

            return address_in_db

        except Exception as error:
            raise UnprocessableEntity(message=f"Failed to create address: {str(error)}")

    async def search_by_cep(self, zip_code: str) -> AddressInDB:
        address_in_db = await self.__address_repository.select_by_zip_code(zip_code=zip_code, raise_404=False)
        if address_in_db:
            return address_in_db

        # If not found,  query ViaCEP
        data = get_address_by_zip_code(zip_code=zip_code)
        if not data or "erro" in data:
            raise NotFoundError(message=f"CEP {zip_code} não encontrado no ViaCEP")

        # Map ViaCEP response to AddressCreate schema
        address_data = AddressCreate(
            zip_code=data["cep"],
            state=data["uf"],
            city=data["localidade"],
            neighborhood=data["bairro"],
            line_1=data["logradouro"],
            line_2=data.get("complemento"),
        )

        return await self.create(address=address_data)

    async def search_all(self) -> List[AddressInDB]:
        return await self.__address_repository.select_all()

    async def delete_by_id(self, id: str) -> AddressInDB:
        return await self.__address_repository.delete_by_id(id=id)
