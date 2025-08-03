import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.crud.pre_orders.schemas import (
    PreOrderCustomer,
    PreOrderInDB,
    PreOrderStatus,
    SelectedOffer,
)
from app.crud.pre_orders.services import PreOrderServices
from app.crud.orders.schemas import Delivery, DeliveryType
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.shared_schemas.payment import PaymentMethod
from app.crud.offers.schemas import OfferInDB


class TestPreOrderServices(unittest.IsolatedAsyncioTestCase):
    async def _pre_order_in_db(self):
        return PreOrderInDB(
            id="pre1",
            organization_id="org1",
            code="001",
            menu_id="men1",
            payment_method=PaymentMethod.CASH,
            customer=PreOrderCustomer(
                name="John",
                ddd="047",
                phone_number="999",
                international_code="55",
            ),
            delivery=Delivery(delivery_type=DeliveryType.WITHDRAWAL),
            observation=None,
            offers=[SelectedOffer(offer_id="off1", quantity=2)],
            status=PreOrderStatus.ACCEPTED,
            tax=0,
            total_amount=10,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
            is_active=True,
        )

    async def test_update_status_calls_repo_and_sends_message(self):
        repo = AsyncMock()
        repo.update_status.return_value = await self._pre_order_in_db()
        customer_repo = AsyncMock()
        offer_repo = AsyncMock()
        org_repo = AsyncMock()
        org_repo.select_by_id.return_value = SimpleNamespace(
            international_code="55", ddd="047", phone_number="999"
        )
        message_srv = AsyncMock()
        service = PreOrderServices(
            pre_order_repository=repo,
            customer_repository=customer_repo,
            offer_repository=offer_repo,
            organization_repository=org_repo,
            message_services=message_srv,
        )
        result = await service.update_status(
            pre_order_id="pre1", new_status=PreOrderStatus.ACCEPTED
        )
        repo.update_status.assert_awaited_with(
            pre_order_id="pre1", new_status=PreOrderStatus.ACCEPTED
        )
        message_srv.create.assert_awaited()
        self.assertEqual(result.status, PreOrderStatus.ACCEPTED)

    async def test_search_by_id_expand_offers(self):
        repo = AsyncMock()
        repo.select_by_id.return_value = await self._pre_order_in_db()
        offer_repo = AsyncMock()
        offer_repo.select_by_id.return_value = OfferInDB(
            id="off1",
            name="Offer1",
            description="d",
            products=[],
            additionals=[],
            file_id=None,
            unit_cost=1.0,
            unit_price=2.0,
            organization_id="org1",
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
            is_active=True,
        )
        service = PreOrderServices(
            pre_order_repository=repo,
            customer_repository=AsyncMock(),
            offer_repository=offer_repo,
            organization_repository=AsyncMock(),
            message_services=AsyncMock(),
        )
        result = await service.search_by_id(id="pre1", expand=["offers"])
        offer_repo.select_by_id.assert_awaited_with(id="off1", raise_404=False)
        self.assertEqual(result.offers[0].id, "off1")
        self.assertEqual(result.offers[0].quantity, 2)

    async def test_search_count(self):
        repo = AsyncMock()
        repo.select_count.return_value = 5
        service = PreOrderServices(
            pre_order_repository=repo,
            customer_repository=AsyncMock(),
            offer_repository=AsyncMock(),
            organization_repository=AsyncMock(),
            message_services=AsyncMock(),
        )
        count = await service.search_count(status=None, code=None)
        self.assertEqual(count, 5)
        repo.select_count.assert_awaited_with(status=None, code=None)

    async def test_delete_by_id(self):
        repo = AsyncMock()
        repo.delete_by_id.return_value = "deleted"
        service = PreOrderServices(
            pre_order_repository=repo,
            customer_repository=AsyncMock(),
            offer_repository=AsyncMock(),
            organization_repository=AsyncMock(),
            message_services=AsyncMock(),
        )
        result = await service.delete_by_id(id="pre1")
        self.assertEqual(result, "deleted")
        repo.delete_by_id.assert_awaited_with(id="pre1")
