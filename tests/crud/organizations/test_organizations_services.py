import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import mongomock
from mongoengine import connect, disconnect

from app.api.exceptions.authentication_exceptions import BadRequestException
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.organizations.repositories import OrganizationRepository
from app.crud.organizations.schemas import (
    Organization,
    OrganizationInDB,
    UpdateOrganization,
    SocialLinks,
)
from app.crud.organizations.services import OrganizationServices
from app.crud.shared_schemas.address import Address
from app.crud.shared_schemas.roles import RoleEnum
from app.crud.shared_schemas.styling import Styling
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
        self.address_service = AsyncMock()
        self.address_service.search_by_cep = AsyncMock(return_value=None)

        self.marketing_email_services = MagicMock()
        self.marketing_email_services.create = AsyncMock(return_value=None)

        self.service = OrganizationServices(
            organization_repository=self.repo,
            user_repository=self.user_repo,
            organization_plan_repository=self.plan_repo,
            address_services=self.address_service,
            cached_complete_users={},
            marketing_email_services=self.marketing_email_services,
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

    async def test_create_sends_email_and_client_message(self):
        owner = await self._user("owner")
        # Ensure user lookups during add_user succeed
        self.user_repo.select_by_id.return_value = owner

        with patch("app.crud.organizations.services.send_email") as send_email_mock, \
             patch.object(OrganizationServices, "send_client_message", new_callable=AsyncMock) as send_msg_mock:

            org = await self.service.create(
                organization=Organization(name="Org Test"),
                owner=owner,
            )

            # Owner added
            self.assertEqual(len(org.users), 1)
            self.assertEqual(org.users[0].user_id, owner.user_id)

            # Email sent
            send_email_mock.assert_called_once()

            # Client message triggered
            send_msg_mock.assert_awaited_once()

            # Marketing email registration executed
            self.marketing_email_services.create.assert_awaited_once()

    async def test_create_subscribes_owner_to_marketing_emails(self):
        owner = await self._user("owner")
        self.user_repo.select_by_id.return_value = owner

        with patch("app.crud.organizations.services.send_email"), \
             patch.object(OrganizationServices, "send_client_message", new_callable=AsyncMock):

            await self.service.create(
                organization=Organization(name="Org Test"),
                owner=owner,
            )

        await_args = self.marketing_email_services.create.await_args
        marketing_email = await_args.args[0] if await_args.args else await_args.kwargs["marketing_email"]
        self.assertEqual(marketing_email.email, owner.email)
        self.assertEqual(marketing_email.name, owner.name)
        self.assertEqual(marketing_email.reason.value, "OTHER")
        self.assertEqual(marketing_email.description, "organization_owner")

    async def test_create_ignores_marketing_subscription_conflict(self):
        owner = await self._user("owner")
        self.user_repo.select_by_id.return_value = owner
        self.marketing_email_services.create.reset_mock()
        self.marketing_email_services.create.side_effect = UnprocessableEntity("exists")

        with patch("app.crud.organizations.services.send_email"), \
             patch.object(OrganizationServices, "send_client_message", new_callable=AsyncMock):
            org = await self.service.create(
                organization=Organization(name="Org Test"),
                owner=owner,
            )

        self.assertIsNotNone(org)
        self.marketing_email_services.create.assert_awaited_once()

    async def test_add_user_subscribes_new_member_to_marketing_emails(self):
        owner = await self._user("owner")
        new_member = await self._user("member")

        org = await self.repo.create(Organization(name="Org"))
        await self.repo.update(
            org.id, {"users": [{"user_id": owner.user_id, "role": RoleEnum.OWNER}]}
        )

        self.user_repo.select_by_id.side_effect = [owner, new_member]

        result = await self.service.add_user(
            organization_id=org.id,
            user_making_request=owner.user_id,
            user_id=new_member.user_id,
            role=RoleEnum.MANAGER,
        )

        self.assertTrue(result)
        self.marketing_email_services.create.assert_awaited()

        await_args = self.marketing_email_services.create.await_args
        marketing_email = await_args.args[0] if await_args.args else await_args.kwargs["marketing_email"]
        self.assertEqual(marketing_email.email, new_member.email)
        self.assertEqual(marketing_email.description, "organization_member")

    async def test_send_client_message_uses_message_services(self):
        owner = await self._user("owner")
        # Create org with phone fields to validate message composition
        org_in_db = await self.repo.create(
            Organization(
                name="My Org",
                international_code="55",
                ddd="047",
                phone_number="999999999",
            )
        )

        with patch("app.crud.organizations.services.MessageServices") as MessageServicesMock:
            instance = MessageServicesMock.return_value
            instance.create = AsyncMock(return_value=True)

            result = await self.service.send_client_message(
                user_in_db=owner,
                organization=org_in_db,
            )

            self.assertTrue(result)
            instance.create.assert_awaited_once()

            # Validate message payload basics
            await_args = instance.create.await_args
            msg = await_args.args[0] if await_args and await_args.args else await_args.kwargs.get("message")
            self.assertIsNotNone(msg)
            self.assertEqual(msg.origin.value, "ORGANIZATIONS")
            # Validator trims leading zero from ddd when BR (55)
            self.assertIn("My Org", msg.message)

    async def test_search_by_id_calls_repo(self):
        org = await self.repo.create(Organization(name="Org"))

        result = await self.service.search_by_id(id=org.id)

        self.assertEqual(result.id, org.id)

    async def test_search_all_calls_repo(self):
        await self.repo.create(Organization(name="Org"))

        result = await self.service.search_all()

        self.assertEqual(len(result), 1)

    async def test_update_styling_and_links(self):
        org = await self.repo.create(Organization(name="Org"))
        await self.repo.update(
            org.id, {"users": [{"user_id": "owner", "role": RoleEnum.OWNER}]}
        )

        self.user_repo.select_by_id.return_value = await self._user("owner")

        update = UpdateOrganization(
            website="https://new.com",
            social_links=SocialLinks(instagram="https://instagram.com/new"),
            styling=Styling(primary_color="#123123", secondary_color="#321321"),
        )

        result = await self.service.update(
            id=org.id, updated_organization=update, user_making_request="owner"
        )

        self.assertEqual(result.website, "https://new.com")
        self.assertEqual(result.social_links.instagram, "https://instagram.com/new")
        self.assertEqual(result.styling.primary_color, "#123123")

    async def test_delete_by_id_not_owner_raises(self):
        org = await self.repo.create(Organization(name="Del"))
        await self.repo.update(
            org.id, {"users": [{"user_id": "admin", "role": RoleEnum.ADMIN}]}
        )

        with self.assertRaises(Exception):
            await self.service.delete_by_id(id=org.id, user_making_request="admin")

    async def test_create_with_invalid_zip_code_raises(self):
        owner = await self._user("owner")
        self.user_repo.select_by_id.return_value = owner
        self.address_service.search_by_cep.side_effect = NotFoundError(message="not found")

        with self.assertRaises(BadRequestException):
            await self.service.create(
                organization=Organization(
                    name="Org Test",
                    address=Address(
                        zip_code="89012-000",
                        city="City",
                        neighborhood="Neighborhood",
                        line_1="Street",
                        number="100",
                    ),
                ),
                owner=owner,
            )

    async def test_update_with_invalid_zip_code_raises(self):
        org = await self.repo.create(Organization(name="Org"))
        await self.repo.update(
            org.id, {"users": [{"user_id": "owner", "role": RoleEnum.OWNER}]}
        )

        self.user_repo.select_by_id.return_value = await self._user("owner")
        self.address_service.search_by_cep.side_effect = NotFoundError(message="not found")

        with self.assertRaises(BadRequestException):
            await self.service.update(
                id=org.id,
                updated_organization=UpdateOrganization(
                    address=Address(
                        zip_code="00000-000",
                        city="City",
                        neighborhood="Neighborhood",
                        line_1="Street",
                        number="10",
                    )
                ),
                user_making_request="owner",
            )

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
