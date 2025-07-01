import unittest
from mongoengine import connect, disconnect
import mongomock

from app.crud.organizations.models import OrganizationModel
from app.crud.organizations.repositories import OrganizationRepository
from app.crud.organizations.schemas import Organization
from app.core.exceptions import NotFoundError, UnprocessableEntity


class TestOrganizationRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        self.repo = OrganizationRepository()

    def tearDown(self):
        disconnect()

    async def _build_org(self, name="Org"):
        return Organization(name=name)

    async def test_create_organization(self):
        org = await self._build_org(name="Org A")

        result = await self.repo.create(org)

        self.assertEqual(result.name, "Org A")
        self.assertEqual(OrganizationModel.objects.count(), 1)

    async def test_create_duplicate_organization_raises_error(self):
        org = await self._build_org(name="Org B")
        await self.repo.create(org)

        with self.assertRaises(UnprocessableEntity):
            await self.repo.create(org)

    async def test_create_strips_whitespace_from_name(self):
        org = await self._build_org(name="  Trim  ")

        result = await self.repo.create(org)

        self.assertEqual(result.name, "Trim")


    async def test_update_organization_name(self):
        org = await self._build_org(name="Old")
        created = await self.repo.create(org)

        updated = await self.repo.update(created.id, {"name": "New"})

        self.assertEqual(updated.name, "New")

    async def test_select_by_id_success(self):
        org = await self.repo.create(await self._build_org())

        result = await self.repo.select_by_id(id=org.id)

        self.assertEqual(result.id, org.id)

    async def test_select_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.select_by_id(id="missing")

    async def test_select_all_filter_by_user(self):
        from app.crud.shared_schemas.roles import RoleEnum
        org1 = await self.repo.create(await self._build_org(name="Org1"))
        org2 = await self.repo.create(await self._build_org(name="Org2"))

        OrganizationModel.objects(id=org1.id).first().update(users=[{"user_id": "u1", "role": RoleEnum.OWNER}])
        OrganizationModel.objects(id=org2.id).first().update(users=[{"user_id": "u2", "role": RoleEnum.OWNER}])

        results = await self.repo.select_all(user_id="u1")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Org1")

    async def test_delete_by_id_success(self):
        created = await self.repo.create(await self._build_org(name="Del"))

        result = await self.repo.delete_by_id(id=created.id)

        self.assertEqual(OrganizationModel.objects(is_active=True).count(), 0)
        self.assertEqual(result.name, "Del")

    async def test_delete_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.delete_by_id(id="missing")

    async def test_select_all_sorted_by_name(self):
        await self.repo.create(await self._build_org(name="Bravo"))
        await self.repo.create(await self._build_org(name="Alpha"))

        results = await self.repo.select_all()

        self.assertEqual([org.name for org in results], ["Alpha", "Bravo"])
