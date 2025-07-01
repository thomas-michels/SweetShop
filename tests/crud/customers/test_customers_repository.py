import unittest
from mongoengine import connect, disconnect
import mongomock

from app.crud.customers.repositories import CustomerRepository
from app.crud.customers.schemas import Customer
from app.crud.customers.models import CustomerModel
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.utils.utc_datetime import UTCDateTime


class TestCustomerRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        self.repo = CustomerRepository(organization_id="org1")

    def tearDown(self):
        disconnect()

    async def _customer(self, name="John Doe", email=None, phone=None):
        data = {
            "name": name,
            "addresses": [],
            "tags": [],
        }
        if email:
            data["email"] = email
        if phone:
            data["ddd"] = "047"
            data["phone_number"] = phone
        return Customer(**data)

    async def test_create_customer(self):
        customer = await self._customer(name="Alice")
        result = await self.repo.create(customer)
        self.assertEqual(result.name, "Alice")
        self.assertEqual(CustomerModel.objects.count(), 1)

    async def test_create_duplicate_email_raises_error(self):
        customer = await self._customer(email="a@test.com")
        await self.repo.create(customer)
        with self.assertRaises(UnprocessableEntity):
            await self.repo.create(await self._customer(name="B", email="a@test.com"))

    async def test_create_duplicate_phone_raises_error(self):
        customer = await self._customer(phone="9999999")
        await self.repo.create(customer)
        with self.assertRaises(UnprocessableEntity):
            await self.repo.create(await self._customer(name="B", phone="9999999"))

    async def test_update_customer_name(self):
        created = await self.repo.create(await self._customer(name="Old"))
        created.name = "New"
        updated = await self.repo.update(created)
        self.assertEqual(updated.name, "New")

    async def test_select_by_id_success(self):
        created = await self.repo.create(await self._customer(name="Find"))
        result = await self.repo.select_by_id(id=created.id)
        self.assertEqual(result.id, created.id)

    async def test_select_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.select_by_id(id="missing")

    async def test_select_count_with_query(self):
        await self.repo.create(await self._customer(name="John"))
        await self.repo.create(await self._customer(name="Johnny"))
        await self.repo.create(await self._customer(name="Mark"))
        count = await self.repo.select_count(query="John")
        self.assertEqual(count, 2)

    async def test_select_all_with_pagination(self):
        await self.repo.create(await self._customer(name="A"))
        await self.repo.create(await self._customer(name="B"))
        await self.repo.create(await self._customer(name="C"))
        results = await self.repo.select_all(query=None, page=1, page_size=2)
        self.assertEqual(len(results), 2)
        results_p2 = await self.repo.select_all(query=None, page=2, page_size=2)
        self.assertEqual(len(results_p2), 1)
        names = {r.name for r in results + results_p2}
        self.assertEqual(names, {"A", "B", "C"})

    async def test_delete_by_id_success(self):
        created = await self.repo.create(await self._customer(name="Del"))
        result = await self.repo.delete_by_id(id=created.id)
        self.assertEqual(CustomerModel.objects(is_active=True).count(), 0)
        self.assertEqual(result.name, "Del")

    async def test_delete_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.delete_by_id(id="missing")



    async def test_select_all_filter_by_tags(self):
        cust1 = await self._customer(name="TaggedA")
        cust1.tags = ["t1", "t2"]
        await self.repo.create(cust1)

        cust2 = await self._customer(name="TaggedB")
        cust2.tags = ["t2"]
        await self.repo.create(cust2)

        results = await self.repo.select_all(query=None, tags=["t1"], page=1, page_size=10)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Taggeda")

    async def test_select_count_returns_zero_when_no_results(self):
        count = await self.repo.select_count(query="Nothing")
        self.assertEqual(count, 0)

    async def test_select_by_phone_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.select_by_phone(ddd="047", phone_number="9999999")

    async def test_select_by_email_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.select_by_email(email="nope@test.com")

    async def test_select_by_name_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.select_by_name(name="Ghost")

    async def test_update_nonexistent_customer_raises_unprocessable(self):
        from app.crud.customers.schemas import CustomerInDB
        missing = CustomerInDB(
            id="missing",
            name="Missing",
            organization_id="org1",
            addresses=[],
            tags=[],
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
            is_active=True,
        )
        with self.assertRaises(UnprocessableEntity):
            await self.repo.update(missing)
