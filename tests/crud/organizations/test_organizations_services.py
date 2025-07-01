import unittest
from unittest.mock import AsyncMock, patch
from mongoengine import connect, disconnect
import mongomock

from app.core.utils.utc_datetime import UTCDateTime
from app.crud.organizations.repositories import OrganizationRepository
from app.crud.organizations.schemas import Organization, OrganizationInDB
from app.crud.organizations.services import OrganizationServices
from app.crud.shared_schemas.roles import RoleEnum
from app.crud.users.schemas import UserInDB


class FakeRedis:
    def delete_value(self, key: str):
        pass


class TestOrganizationServices(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        self.repo = OrganizationRepository()
        self.user_repo = AsyncMock()
        self.plan_repo = AsyncMock()
        patcher = patch("app.crud.organizations.services.RedisManager", return_value=FakeRedis())
        self.addCleanup(patcher.stop)
        patcher.start()
        self.service = OrganizationServices(
            organization_repository=self.repo,
            user_repository=self.user_repo,
            organization_plan_repository=self.plan_repo,
        )

    def tearDown(self):
        disconnect()

    async def _user(self, user_id="user1"):
        return UserInDB(
            user_id=user_id,
            email=f"{user_id}@test.com",
            name="Test",
            nickname="Test",
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )

    async def test_search_by_id_calls_repo(self):
        org = await self.repo.create(Organization(name="Org"))

        result = await self.service.search_by_id(id=org.id)

        self.assertEqual(result.id, org.id)

    async def test_search_all_calls_repo(self):
        await self.repo.create(Organization(name="Org"))

        result = await self.service.search_all()

        self.assertEqual(len(result), 1)

    async def test_delete_by_id_authorized(self):
        org = await self.repo.create(Organization(name="Del"))
        await self.repo.update(org.id, {"users": [{"user_id": "owner", "role": RoleEnum.OWNER}]})

        self.repo.delete_by_id = AsyncMock(return_value=OrganizationInDB(id=org.id, name=org.name, users=[], created_at=UTCDateTime.now(), updated_at=UTCDateTime.now()))

        result = await self.service.delete_by_id(id=org.id, user_making_request="owner")

        self.assertEqual(result.id, org.id)
        self.repo.delete_by_id.assert_awaited_with(id=org.id)

    async def test_delete_by_id_not_owner_raises(self):
        org = await self.repo.create(Organization(name="Del"))
        await self.repo.update(org.id, {"users": [{"user_id": "admin", "role": RoleEnum.ADMIN}]})

        with self.assertRaises(Exception):
            await self.service.delete_by_id(id=org.id, user_making_request="admin")

    async def test_add_user_success(self):
        org = await self.repo.create(Organization(name="Org"))
        await self.repo.update(org.id, {"users": [{"user_id": "owner", "role": RoleEnum.OWNER}]})

        async def _select(*args, **kwargs):
            user_id = args[0] if args else kwargs.get("id")
            return await self._user(user_id)

        self.user_repo.select_by_id.side_effect = _select

        result = await self.service.add_user(
            organization_id=org.id,
            user_making_request="owner",
            user_id="member",
            role=RoleEnum.ADMIN,
        )

        self.assertTrue(result)
        updated = await self.service.search_by_id(id=org.id)
        self.assertEqual(len(updated.users), 2)

