import unittest
import sys
import types
from unittest.mock import AsyncMock, MagicMock, patch

import mongomock
from mongoengine import connect, disconnect

if "boto3" not in sys.modules:
    boto3_module = types.ModuleType("boto3")
    boto3_module.client = MagicMock(return_value=MagicMock())
    boto3_module.resource = MagicMock(return_value=MagicMock())

    boto3_s3_module = types.ModuleType("boto3.s3")
    boto3_transfer_module = types.ModuleType("boto3.s3.transfer")
    boto3_transfer_module.S3Transfer = MagicMock()

    sys.modules["boto3"] = boto3_module
    sys.modules["boto3.s3"] = boto3_s3_module
    sys.modules["boto3.s3.transfer"] = boto3_transfer_module

if "PIL" not in sys.modules:
    pil_module = types.ModuleType("PIL")
    pil_module.Image = MagicMock()
    pil_module.ImageOps = MagicMock()
    pil_module.UnidentifiedImageError = Exception
    pil_module.ImageFile = MagicMock()
    sys.modules["PIL"] = pil_module

if "resend" not in sys.modules:
    resend_module = types.ModuleType("resend")
    resend_module.Emails = MagicMock()
    resend_module.api_key = None
    sys.modules["resend"] = resend_module

if "redis" not in sys.modules:
    redis_module = types.ModuleType("redis")
    redis_module.Redis = MagicMock(return_value=MagicMock())
    sys.modules["redis"] = redis_module

if "geopy" not in sys.modules:
    geopy_module = types.ModuleType("geopy")
    geopy_geocoders_module = types.ModuleType("geopy.geocoders")
    geopy_exc_module = types.ModuleType("geopy.exc")
    geopy_geocoders_module.Nominatim = MagicMock(return_value=MagicMock())
    geopy_exc_module.GeocoderTimedOut = Exception
    geopy_exc_module.GeocoderUnavailable = Exception
    sys.modules["geopy"] = geopy_module
    sys.modules["geopy.geocoders"] = geopy_geocoders_module
    sys.modules["geopy.exc"] = geopy_exc_module

from app.api.exceptions.authentication_exceptions import BadRequestException, UnauthorizedException
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.invoices.repositories import InvoiceRepository
from app.crud.invoices.schemas import InvoiceStatus
from app.crud.invoices.services import InvoiceServices
from app.crud.organization_plans.schemas import OrganizationPlanInDB
from app.crud.organization_plans.repositories import OrganizationPlanRepository
from app.crud.organization_plans.services import OrganizationPlanServices
from app.crud.organizations.repositories import OrganizationRepository
from app.crud.organizations.schemas import (
    Organization,
    OrganizationInDB,
    UpdateOrganization,
    SocialLinks,
)
from app.crud.plan_features.repositories import PlanFeatureRepository
from app.crud.plans.schemas import Plan
from app.crud.plans.repositories import PlanRepository
from app.crud.plans.services import PlanServices
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

        self.organization_plan_repository = OrganizationPlanRepository(cache_plans={})
        self.plan_repository = PlanRepository()
        self.plan_services = PlanServices(
            plan_repository=self.plan_repository,
            plan_feature_repository=PlanFeatureRepository(),
        )
        self.organization_plan_services = OrganizationPlanServices(
            organization_plan_repository=self.organization_plan_repository,
            plan_repository=self.plan_repository,
        )
        self.invoice_repository = InvoiceRepository()
        self.invoice_services = InvoiceServices(
            invoice_repository=self.invoice_repository,
            organization_plan_repository=self.organization_plan_repository,
        )

        self.service = OrganizationServices(
            organization_repository=self.repo,
            user_repository=self.user_repo,
            organization_plan_repository=self.organization_plan_repository,
            address_services=self.address_service,
            cached_complete_users={},
            plan_services=self.plan_services,
            organization_plan_services=self.organization_plan_services,
            invoice_services=self.invoice_services,
            marketing_email_services=self.marketing_email_services,
        )

    def tearDown(self):
        disconnect()

    def _wrap_repo_update_without_plan(self):
        orig_update = self.repo.update

        async def safe_update(*args, **kwargs):
            org_dict = kwargs.get("organization") if "organization" in kwargs else args[1]
            org_dict.pop("plan", None)
            return await orig_update(*(args if args else [kwargs["organization_id"], org_dict]))

        self.repo.update = safe_update

    async def _user(self, user_id="user1"):
        return UserInDB(
            user_id=user_id,
            email=f"{user_id}@test.com",
            name="Test",
            nickname="Test",
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )

    async def _create_premium_plan(self):
        return await self.plan_services.create(
            Plan(name="Premium", description="Premium trial", price=99.9)
        )

    async def _get_trial_plan_with_invoice(self, organization_id: str) -> OrganizationPlanInDB:
        organization_plans = await self.organization_plan_services.search_all(
            organization_id=organization_id
        )
        self.assertEqual(len(organization_plans), 1)

        invoices = await self.invoice_services.search_by_organization_plan_id(
            organization_plan_id=organization_plans[0].id
        )
        self.assertEqual(len(invoices), 1)

        organization_plans[0].has_paid_invoice = invoices[0].status == InvoiceStatus.PAID
        return organization_plans[0]

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

    async def test_create_full_success_flow(self):
        premium_plan = await self._create_premium_plan()
        owner = await self._user("owner")
        self.user_repo.select_by_id.return_value = owner

        with patch("app.crud.organizations.services.send_email") as send_email_mock, \
             patch.object(OrganizationServices, "send_client_message", new_callable=AsyncMock, return_value=True) as send_msg_mock:
            org = await self.service.create(
                organization=Organization(name="Org Full Flow"),
                owner=owner,
            )

        self.assertIsNotNone(org.id)
        self.assertEqual(org.name, "Org Full Flow")
        self.assertEqual(len(org.users), 1)
        self.assertEqual(org.users[0].user_id, owner.user_id)
        self.assertEqual(org.users[0].role, RoleEnum.OWNER)

        persisted_org = await self.service.search_by_id(id=org.id)
        self.assertEqual(len(persisted_org.users), 1)
        self.assertEqual(persisted_org.users[0].user_id, owner.user_id)
        self.assertEqual(persisted_org.users[0].role, RoleEnum.OWNER)

        active_plan = await self._get_trial_plan_with_invoice(organization_id=org.id)
        self.assertEqual(active_plan.plan_id, premium_plan.id)
        self.assertTrue(active_plan.has_paid_invoice)
        self.assertEqual((active_plan.end_date - active_plan.start_date).days, 60)

        send_email_mock.assert_called_once()
        send_email_kwargs = send_email_mock.call_args.kwargs
        self.assertEqual(send_email_kwargs["email_to"], [owner.email])
        self.assertIn("Bem-vindo", send_email_kwargs["title"])
        self.assertIn(owner.name.title(), send_email_kwargs["message"])

        send_msg_mock.assert_awaited_once()
        send_msg_kwargs = send_msg_mock.await_args.kwargs
        self.assertEqual(send_msg_kwargs["user_in_db"].user_id, owner.user_id)
        self.assertEqual(send_msg_kwargs["organization"].id, org.id)

        self.marketing_email_services.create.assert_awaited_once()
        marketing_email_args = self.marketing_email_services.create.await_args
        marketing_email = (
            marketing_email_args.args[0]
            if marketing_email_args.args
            else marketing_email_args.kwargs["marketing_email"]
        )
        self.assertEqual(marketing_email.email, owner.email)
        self.assertEqual(marketing_email.description, "organization_owner")

    async def test_create_subscribes_owner_to_marketing_emails(self):
        await self._create_premium_plan()
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
        await self._create_premium_plan()
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

    async def test_create_provisions_premium_trial_with_paid_invoice(self):
        await self._create_premium_plan()
        owner = await self._user("owner")
        self.user_repo.select_by_id.return_value = owner

        with patch("app.crud.organizations.services.send_email"), \
             patch.object(OrganizationServices, "send_client_message", new_callable=AsyncMock):
            org = await self.service.create(
                organization=Organization(name="Org Trial"),
                owner=owner,
            )

        active_plan = await self._get_trial_plan_with_invoice(organization_id=org.id)
        self.assertIsNotNone(active_plan)
        self.assertEqual(active_plan.plan_id, (await self.plan_services.search_by_name("Premium")).id)
        self.assertTrue(active_plan.has_paid_invoice)
        invoices = await self.invoice_services.search_by_organization_plan_id(organization_plan_id=active_plan.id)
        self.assertEqual(invoices[0].status, InvoiceStatus.PAID)
        self.assertEqual(invoices[0].amount, 0)
        self.assertEqual(invoices[0].amount_paid, 0)
        self.assertEqual(
            invoices[0].observation["reason"],
            "organization_creation_premium_trial",
        )
        self.assertEqual((active_plan.end_date - active_plan.start_date).days, 60)

    async def test_create_with_premium_trial_is_immediately_visible_in_expanded_plan(self):
        await self._create_premium_plan()
        owner = await self._user("owner")
        self.user_repo.select_by_id.return_value = owner

        with patch("app.crud.organizations.services.send_email"), \
             patch.object(OrganizationServices, "send_client_message", new_callable=AsyncMock):
            org = await self.service.create(
                organization=Organization(name="Org Trial"),
                owner=owner,
            )

        active_plan = await self._get_trial_plan_with_invoice(organization_id=org.id)

        with patch.object(
            self.organization_plan_repository,
            "select_active_plan",
            new=AsyncMock(return_value=active_plan),
        ):
            complete_org = await self.service.search_by_id(id=org.id, expand=["plan"])

        self.assertIsNotNone(complete_org.plan)
        self.assertEqual(complete_org.plan.plan_id, active_plan.plan_id)
        self.assertTrue(complete_org.plan.has_paid_invoice)
        self.assertGreater(complete_org.plan.end_date, UTCDateTime.now())

    async def test_create_without_premium_plan_keeps_organization_creation(self):
        owner = await self._user("owner")
        self.user_repo.select_by_id.return_value = owner

        with patch("app.crud.organizations.services.send_email"), \
             patch.object(OrganizationServices, "send_client_message", new_callable=AsyncMock), \
             patch("app.crud.organizations.services.logger.warning") as logger_warning:
            org = await self.service.create(
                organization=Organization(name="Org Without Premium"),
                owner=owner,
            )

        self.assertIsNotNone(org)
        logger_warning.assert_called()

    async def test_create_logs_and_keeps_organization_when_trial_plan_creation_fails(self):
        await self._create_premium_plan()
        owner = await self._user("owner")
        self.user_repo.select_by_id.return_value = owner

        with patch("app.crud.organizations.services.send_email"), \
             patch.object(OrganizationServices, "send_client_message", new_callable=AsyncMock), \
             patch.object(
                 self.organization_plan_services,
                 "create",
                 new=AsyncMock(side_effect=Exception("plan failure")),
             ), \
             patch("app.crud.organizations.services.logger.error") as logger_error:
            org = await self.service.create(
                organization=Organization(name="Org Plan Failure"),
                owner=owner,
            )

        self.assertIsNotNone(org)
        logger_error.assert_called()

    async def test_create_logs_and_keeps_organization_when_trial_invoice_creation_fails(self):
        await self._create_premium_plan()
        owner = await self._user("owner")
        self.user_repo.select_by_id.return_value = owner

        with patch("app.crud.organizations.services.send_email"), \
             patch.object(OrganizationServices, "send_client_message", new_callable=AsyncMock), \
             patch.object(
                 self.invoice_services,
                 "create",
                 new=AsyncMock(side_effect=Exception("invoice failure")),
             ), \
             patch("app.crud.organizations.services.logger.error") as logger_error:
            org = await self.service.create(
                organization=Organization(name="Org Invoice Failure"),
                owner=owner,
            )

        self.assertIsNotNone(org)
        logger_error.assert_called()

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

    async def test_search_by_id_with_expand_populates_users_plan_and_file(self):
        org = await self.repo.create(Organization(name="Org", file_id="file-1"))
        await self.repo.update(
            org.id, {"users": [{"user_id": "owner", "role": RoleEnum.OWNER}]}
        )
        user = await self._user("owner")
        active_plan = MagicMock(id="plan-1")
        file_in_db = MagicMock(id="file-1")

        with patch.object(self.user_repo, "select_by_id", new=AsyncMock(return_value=user)), \
             patch.object(self.organization_plan_repository, "select_active_plan", new=AsyncMock(return_value=active_plan)), \
             patch("app.crud.organizations.services.FileRepository.select_by_id", new=AsyncMock(return_value=file_in_db)):
            result = await self.service.search_by_id(id=org.id, expand=["users", "plan", "file"])

        self.assertEqual(result.users[0].user.email, user.email)
        self.assertEqual(result.plan.id, active_plan.id)
        self.assertEqual(result.file.id, file_in_db.id)

    async def test_search_all_calls_repo(self):
        await self.repo.create(Organization(name="Org"))

        result = await self.service.search_all()

        self.assertEqual(len(result), 1)

    async def test_check_if_can_add_more_users_raises_when_limit_reached(self):
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

        plan_feature = MagicMock(value="3")
        with patch("app.crud.organizations.services.get_plan_feature", new=AsyncMock(return_value=plan_feature)):
            with self.assertRaises(UnauthorizedException):
                await self.service.check_if_can_add_more_users(organization_id=org.id)

    async def test_check_if_can_add_more_users_raises_when_plan_feature_is_missing(self):
        org = await self.repo.create(Organization(name="Org"))

        with patch("app.crud.organizations.services.get_plan_feature", new=AsyncMock(return_value=None)):
            with self.assertRaises(UnauthorizedException):
                await self.service.check_if_can_add_more_users(organization_id=org.id)

    async def test_update_denies_non_admin_or_owner(self):
        org = await self.repo.create(Organization(name="Org"))
        await self.repo.update(
            org.id, {"users": [{"user_id": "member", "role": RoleEnum.MEMBER}]}
        )

        with self.assertRaises(UnauthorizedException):
            await self.service.update(
                id=org.id,
                updated_organization=UpdateOrganization(name="New Name"),
                user_making_request="member",
            )

    async def test_update_rejects_invalid_file_purpose(self):
        org = await self.repo.create(Organization(name="Org"))
        await self.repo.update(
            org.id, {"users": [{"user_id": "owner", "role": RoleEnum.OWNER}]}
        )

        invalid_file = MagicMock(purpose="PRODUCTS")
        with patch("app.crud.organizations.services.FileRepository.select_by_id", new=AsyncMock(return_value=invalid_file)):
            with self.assertRaises(BadRequestException):
                await self.service.update(
                    id=org.id,
                    updated_organization=UpdateOrganization(file_id="file-123"),
                    user_making_request="owner",
                )

    async def test_update_without_changes_does_not_persist(self):
        org = await self.repo.create(Organization(name="Org"))
        await self.repo.update(
            org.id, {"users": [{"user_id": "owner", "role": RoleEnum.OWNER}]}
        )
        self.repo.update = AsyncMock(side_effect=self.repo.update)

        result = await self.service.update(
            id=org.id,
            updated_organization=UpdateOrganization(),
            user_making_request="owner",
        )

        self.assertEqual(result.id, org.id)
        self.repo.update.assert_not_awaited()

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

        with self.assertRaises(UnauthorizedException):
            await self.service.delete_by_id(id=org.id, user_making_request="admin")

    async def test_delete_by_id_returns_none_when_user_is_not_in_organization(self):
        org = await self.repo.create(Organization(name="Del"))
        await self.repo.update(
            org.id, {"users": [{"user_id": "owner", "role": RoleEnum.OWNER}]}
        )

        result = await self.service.delete_by_id(id=org.id, user_making_request="stranger")

        self.assertIsNone(result)

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

    async def test_create_rolls_back_when_owner_cannot_be_added(self):
        owner = await self._user("owner")

        with patch.object(self.service, "add_user", new=AsyncMock(return_value=False)):
            with self.assertRaises(UnprocessableEntity):
                await self.service.create(
                    organization=Organization(name="Org Test"),
                    owner=owner,
                )

        self.assertEqual(await self.repo.select_all(), [])

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

    async def test_add_user_denies_member_requester(self):
        org = await self.repo.create(Organization(name="Org"))
        await self.repo.update(
            org.id,
            {
                "users": [
                    {"user_id": "member-requester", "role": RoleEnum.MEMBER},
                    {"user_id": "target", "role": RoleEnum.MEMBER},
                ]
            },
        )

        async def _select(*args, **kwargs):
            user_id = args[0] if args else kwargs.get("id")
            return await self._user(user_id)

        self.user_repo.select_by_id.side_effect = _select

        with self.assertRaises(UnauthorizedException):
            await self.service.add_user(
                organization_id=org.id,
                user_making_request="member-requester",
                user_id="target",
                role=RoleEnum.MANAGER,
            )

    async def test_add_user_denies_requester_outside_organization(self):
        org = await self.repo.create(Organization(name="Org"))
        await self.repo.update(
            org.id, {"users": [{"user_id": "target", "role": RoleEnum.MEMBER}]}
        )

        async def _select(*args, **kwargs):
            user_id = args[0] if args else kwargs.get("id")
            return await self._user(user_id)

        self.user_repo.select_by_id.side_effect = _select

        with self.assertRaises(UnauthorizedException):
            await self.service.add_user(
                organization_id=org.id,
                user_making_request="outsider",
                user_id="target",
                role=RoleEnum.MANAGER,
            )

    async def test_add_user_allows_external_self_add_when_invited(self):
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
            user_making_request="invited-user",
            user_id="invited-user",
            role=RoleEnum.MEMBER,
            allow_external_self_add=True,
        )

        self.assertTrue(result)
        updated = await self.service.search_by_id(id=org.id)
        self.assertEqual(len(updated.users), 2)
        self.assertEqual(updated.get_user_in_organization("invited-user").role, RoleEnum.MEMBER)

    async def test_add_user_denies_promoting_manager_to_owner(self):
        org = await self.repo.create(Organization(name="Org"))
        await self.repo.update(
            org.id,
            {
                "users": [
                    {"user_id": "owner", "role": RoleEnum.OWNER},
                    {"user_id": "manager", "role": RoleEnum.MANAGER},
                ]
            },
        )

        async def _select(*args, **kwargs):
            user_id = args[0] if args else kwargs.get("id")
            return await self._user(user_id)

        self.user_repo.select_by_id.side_effect = _select

        with self.assertRaises(UnauthorizedException):
            await self.service.add_user(
                organization_id=org.id,
                user_making_request="owner",
                user_id="manager",
                role=RoleEnum.OWNER,
            )

    async def test_add_user_updates_existing_user_without_duplication(self):
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

        async def _select(*args, **kwargs):
            user_id = args[0] if args else kwargs.get("id")
            return await self._user(user_id)

        self.user_repo.select_by_id.side_effect = _select

        result = await self.service.add_user(
            organization_id=org.id,
            user_making_request="owner",
            user_id="admin",
            role=RoleEnum.MANAGER,
        )

        self.assertTrue(result)
        updated = await self.service.search_by_id(id=org.id)
        self.assertEqual(len(updated.users), 2)
        self.assertEqual(updated.get_user_in_organization("admin").role, RoleEnum.MANAGER)

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

        self._wrap_repo_update_without_plan()

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

    async def test_update_user_role_denies_manager_assigning_admin(self):
        org = await self.repo.create(Organization(name="Org"))
        await self.repo.update(
            org.id,
            {
                "users": [
                    {"user_id": "manager", "role": RoleEnum.MANAGER},
                    {"user_id": "member", "role": RoleEnum.MEMBER},
                ]
            },
        )

        async def _select(*args, **kwargs):
            user_id = args[0] if args else kwargs.get("id")
            return await self._user(user_id)

        self.user_repo.select_by_id.side_effect = _select

        with self.assertRaises(UnauthorizedException):
            await self.service.update_user_role(
                organization_id=org.id,
                user_making_request="manager",
                user_id="member",
                role=RoleEnum.ADMIN,
            )

    async def test_update_user_role_denies_when_target_user_is_missing_from_organization(self):
        org = await self.repo.create(Organization(name="Org"))
        await self.repo.update(
            org.id, {"users": [{"user_id": "owner", "role": RoleEnum.OWNER}]}
        )

        async def _select(*args, **kwargs):
            user_id = args[0] if args else kwargs.get("id")
            return await self._user(user_id)

        self.user_repo.select_by_id.side_effect = _select

        with self.assertRaises(UnauthorizedException):
            await self.service.update_user_role(
                organization_id=org.id,
                user_making_request="owner",
                user_id="ghost",
                role=RoleEnum.MEMBER,
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

        self._wrap_repo_update_without_plan()

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

    async def test_remove_user_denies_admin_removing_admin(self):
        org = await self.repo.create(Organization(name="Org"))
        await self.repo.update(
            org.id,
            {
                "users": [
                    {"user_id": "owner", "role": RoleEnum.OWNER},
                    {"user_id": "admin-requester", "role": RoleEnum.ADMIN},
                    {"user_id": "admin-target", "role": RoleEnum.ADMIN},
                ]
            },
        )

        async def _select(*args, **kwargs):
            user_id = args[0] if args else kwargs.get("id")
            return await self._user(user_id)

        self.user_repo.select_by_id.side_effect = _select

        with self.assertRaises(UnauthorizedException):
            await self.service.remove_user(
                organization_id=org.id,
                user_making_request="admin-requester",
                user_id="admin-target",
            )

    async def test_remove_user_denies_requester_outside_organization(self):
        org = await self.repo.create(Organization(name="Org"))
        await self.repo.update(
            org.id, {"users": [{"user_id": "member", "role": RoleEnum.MEMBER}]}
        )

        async def _select(*args, **kwargs):
            user_id = args[0] if args else kwargs.get("id")
            return await self._user(user_id)

        self.user_repo.select_by_id.side_effect = _select

        with self.assertRaises(UnauthorizedException):
            await self.service.remove_user(
                organization_id=org.id,
                user_making_request="outsider",
                user_id="member",
            )

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

        self._wrap_repo_update_without_plan()

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

    async def test_transfer_ownership_denies_when_target_is_not_admin(self):
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

        async def _select(*args, **kwargs):
            user_id = args[0] if args else kwargs.get("id")
            return await self._user(user_id)

        self.user_repo.select_by_id.side_effect = _select

        with self.assertRaises(UnauthorizedException):
            await self.service.transfer_ownership(
                organization_id=org.id,
                user_making_request="owner",
                user_id="member",
            )

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

        self._wrap_repo_update_without_plan()

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

    async def test_leave_organization_denies_owner_when_other_users_exist(self):
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

        self.user_repo.select_by_id.return_value = await self._user("owner")

        with self.assertRaises(UnauthorizedException):
            await self.service.leave_the_organization(
                organization_id=org.id,
                user_id="owner",
            )

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

    async def test_clear_user_cache_returns_expected_flag(self):
        service = OrganizationServices(
            organization_repository=self.repo,
            user_repository=self.user_repo,
            organization_plan_repository=self.organization_plan_repository,
            address_services=self.address_service,
            cached_complete_users={"user-1": MagicMock()},
        )

        self.assertTrue(service.clear_user_cache("user-1"))
        self.assertFalse(service.clear_user_cache("user-1"))

    async def test_add_user_continues_when_marketing_subscription_fails(self):
        owner = await self._user("owner")
        new_member = await self._user("member")
        org = await self.repo.create(Organization(name="Org"))
        await self.repo.update(
            org.id, {"users": [{"user_id": owner.user_id, "role": RoleEnum.OWNER}]}
        )

        self.user_repo.select_by_id.side_effect = [owner, new_member]
        self.marketing_email_services.create.side_effect = Exception("marketing unavailable")

        with patch("app.crud.organizations.services.logger.error") as logger_error:
            result = await self.service.add_user(
                organization_id=org.id,
                user_making_request=owner.user_id,
                user_id=new_member.user_id,
                role=RoleEnum.MEMBER,
            )

        self.assertTrue(result)
        logger_error.assert_called()
