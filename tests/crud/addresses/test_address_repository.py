import unittest
import mongomock
from bson import ObjectId
from mongoengine import connect, disconnect

from app.crud.addresses.schemas import AddressCreate, AddressUpdate
from app.crud.addresses.repositories import AddressRepository
from app.core.exceptions import NotFoundError

class TestAddressRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        self.repo = AddressRepository()

    def tearDown(self):
        disconnect()

    async def test_create_and_select_by_zip_code(self):
        address = AddressCreate(
            zip_code="01001-000",
            state="SP",
            city="São Paulo",
            neighborhood="Sé",
            line_1="Praça da Sé",
            line_2=None,
            number=None,
        )
        created = await self.repo.create(address=address)
        self.assertEqual(created.zip_code, address.zip_code)
        self.assertEqual(created.state, address.state)

        found = await self.repo.select_by_zip_code(zip_code="01001-000")
        self.assertEqual(found.id, created.id)
        self.assertEqual(found.state, address.state)

    async def test_select_by_zip_code_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.select_by_zip_code(zip_code="99999999")

    async def test_update_address(self):
        address = AddressCreate(
            zip_code="01001000",
            state="SP",
            city="Sao Paulo",
            neighborhood="Se",
            line_1="Praca da Se",
            line_2=None,
            number=None,
        )
        created = await self.repo.create(address=address)

        update_data = AddressUpdate(
            city="Campinas",
            line_2="Apto 101",
            zip_code="13083-852",
        )
        updated = await self.repo.update(id=created.id, address=update_data)

        self.assertEqual(updated.id, created.id)
        self.assertEqual(updated.city, "Campinas")
        self.assertEqual(updated.line_2, "Apto 101")
        self.assertEqual(updated.zip_code, "13083852")

    async def test_update_address_not_found(self):
        update_data = AddressUpdate(city="Campinas")

        with self.assertRaises(NotFoundError):
            await self.repo.update(id=str(ObjectId()), address=update_data)

if __name__ == "__main__":
    unittest.main()
