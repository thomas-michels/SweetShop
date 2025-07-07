import unittest
from unittest.mock import AsyncMock

import mongomock
from mongoengine import connect, disconnect

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
        self.service = OrganizationServices(
            organization_repository=self.repo,
            user_repository=self.user_repo,
            organization_plan_repository=self.plan_repo,
            cached_complete_users={},
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
        await self.repo.update(
            org.id, {"users": [{"user_id": "owner", "role": RoleEnum.OWNER}]}
        )

        self.repo.delete_by_id = AsyncMock(
            return_value=OrganizationInDB(
                id=org.id,
                name=org.name,
                users=[],
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
            )
        )

        result = await self.service.delete_by_id(id=org.id, user_making_request="owner")

        self.assertEqual(result.id, org.id)
        self.repo.delete_by_id.assert_awaited_with(id=org.id)

    async def test_delete_by_id_not_owner_raises(self):
        org = await self.repo.create(Organization(name="Del"))
        await self.repo.update(
            org.id, {"users": [{"user_id": "admin", "role": RoleEnum.ADMIN}]}
        )

        with self.assertRaises(Exception):
            await self.service.delete_by_id(id=org.id, user_making_request="admin")

    async def test_add_user_success(self):
        org = await self.repo.create(Organization(name="Org"))
        await self.repo.update(
            org.id, {"users": [{"user_id": "owner", "role": RoleEnum.OWNER}]}
        )

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

    async def test_update_user_role_success(self):
        org = await self.repo.create(Organization(name="Org"))
        await self.repo.update(
            org.id,
            {
                "users": [
                    {"user_id": "owner", "role": RoleEnum.OWNER},
                    {"user_id": "admin", "role": RoleEnum.ADMIN},
                ]
            },
        )

        orig_update = self.repo.update

        async def safe_update(*args, **kwargs):
            org_dict = (
                kwargs.get("organization") if "organization" in kwargs else args[1]
            )
            org_dict.pop("plan", None)
            return await orig_update(
                *(args if args else [kwargs["organization_id"], org_dict])
            )

        self.repo.update = safe_update

        async def _select(*args, **kwargs):
            user_id = args[0] if args else kwargs.get("id")
            return await self._user(user_id)

        self.user_repo.select_by_id.side_effect = _select

        result = await self.service.update_user_role(
            organization_id=org.id,
            user_making_request="owner",
            user_id="admin",
            role=RoleEnum.MANAGER,
        )

        self.assertTrue(result)
        updated = await self.service.search_by_id(id=org.id)
        self.assertEqual(
            updated.get_user_in_organization("admin").role,
            RoleEnum.MANAGER,
        )

    async def test_remove_user_as_owner(self):
        org = await self.repo.create(Organization(name="Org"))
        await self.repo.update(
            org.id,
            {
                "users": [
                    {"user_id": "owner", "role": RoleEnum.OWNER},
                    {"user_id": "member", "role": RoleEnum.MEMBER},
                ]
            },
        )

        orig_update = self.repo.update

        async def safe_update(*args, **kwargs):
            org_dict = (
                kwargs.get("organization") if "organization" in kwargs else args[1]
            )
            org_dict.pop("plan", None)
            return await orig_update(
                *(args if args else [kwargs["organization_id"], org_dict])
            )

        self.repo.update = safe_update

        async def _select(*args, **kwargs):
            user_id = args[0] if args else kwargs.get("id")
            return await self._user(user_id)

        self.user_repo.select_by_id.side_effect = _select

        result = await self.service.remove_user(
            organization_id=org.id,
            user_making_request="owner",
            user_id="member",
        )

        self.assertTrue(result)
        updated = await self.service.search_by_id(id=org.id)
        self.assertEqual(len(updated.users), 1)

    async def test_transfer_ownership(self):
        org = await self.repo.create(Organization(name="Org"))
        await self.repo.update(
            org.id,
            {
                "users": [
                    {"user_id": "owner", "role": RoleEnum.OWNER},
                    {"user_id": "admin", "role": RoleEnum.ADMIN},
                ]
            },
        )

        orig_update = self.repo.update

        async def safe_update(*args, **kwargs):
            org_dict = (
                kwargs.get("organization") if "organization" in kwargs else args[1]
            )
            org_dict.pop("plan", None)
            return await orig_update(
                *(args if args else [kwargs["organization_id"], org_dict])
            )

        self.repo.update = safe_update

        async def _select(*args, **kwargs):
            user_id = args[0] if args else kwargs.get("id")
            return await self._user(user_id)

        self.user_repo.select_by_id.side_effect = _select

        result = await self.service.transfer_ownership(
            organization_id=org.id,
            user_making_request="owner",
            user_id="admin",
        )

        self.assertTrue(result)
        updated = await self.service.search_by_id(id=org.id)
        self.assertEqual(updated.get_user_in_organization("admin").role, RoleEnum.OWNER)
        self.assertEqual(updated.get_user_in_organization("owner").role, RoleEnum.ADMIN)

    async def test_leave_organization_removes_user(self):
        org = await self.repo.create(Organization(name="Org"))
        await self.repo.update(
            org.id,
            {
                "users": [
                    {"user_id": "owner", "role": RoleEnum.OWNER},
                    {"user_id": "member", "role": RoleEnum.MEMBER},
                ]
            },
        )

        orig_update = self.repo.update

        async def safe_update(*args, **kwargs):
            org_dict = (
                kwargs.get("organization") if "organization" in kwargs else args[1]
            )
            org_dict.pop("plan", None)
            return await orig_update(
                *(args if args else [kwargs["organization_id"], org_dict])
            )

        self.repo.update = safe_update

        async def _select(*args, **kwargs):
            user_id = args[0] if args else kwargs.get("id")
            return await self._user(user_id)

        self.user_repo.select_by_id.side_effect = _select

        result = await self.service.leave_the_organization(
            organization_id=org.id,
            user_id="member",
        )

        self.assertTrue(result)
        updated = await self.service.search_by_id(id=org.id)
        self.assertEqual(len(updated.users), 1)

    async def test_leave_organization_deletes_when_last_user(self):
        org = await self.repo.create(Organization(name="Solo"))
        await self.repo.update(
            org.id,
            {
                "users": [
                    {"user_id": "owner", "role": RoleEnum.OWNER},
                ]
            },
        )

        async def _select(*args, **kwargs):
            user_id = args[0] if args else kwargs.get("id")
            return await self._user(user_id)

        self.user_repo.select_by_id.side_effect = _select

        result = await self.service.leave_the_organization(
            organization_id=org.id,
            user_id="owner",
        )

        self.assertIsInstance(result, OrganizationInDB)
        self.assertEqual(await self.repo.select_all(), [])
