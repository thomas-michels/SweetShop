import unittest
from unittest.mock import AsyncMock
from mongoengine import connect, disconnect
import mongomock

from app.core.utils.utc_datetime import UTCDateTime
from app.crud.offers.repositories import OfferRepository
from app.crud.offers.schemas import (
    OfferProduct,
    RequestOffer,
    Additional,
    UpdateOffer,
    OfferInDB,
)
from app.crud.offers.services import OfferServices
from app.crud.products.schemas import ProductInDB


class TestOfferServices(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        repo = OfferRepository(organization_id="org1")
        self.product_repo = AsyncMock()
        self.file_repo = AsyncMock()
        self.service = OfferServices(
            offer_repository=repo,
            product_repository=self.product_repo,
            file_repository=self.file_repo,
        )

    def tearDown(self):
        disconnect()

    async def _product_in_db(self):
        return ProductInDB(
            id="p1",
            name="P1",
            description="d",
            unit_cost=1.0,
            unit_price=2.0,
            tags=[],
            file_id=None,
            organization_id="org1",
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
            is_active=True,
        )

    async def _request_offer(self):
        return RequestOffer(
            name="Combo",
            description="desc",
            products=["p1"],
            additionals=[
                Additional(
                    name="Bacon",
                    unit_price=0.5,
                    unit_cost=0.3,
                    min_quantity=1,
                    max_quantity=2,
                )
            ],
        )

    async def test_create_offer_with_additionals(self):
        self.product_repo.select_by_id.return_value = await self._product_in_db()
        result = await self.service.create(await self._request_offer())
        self.assertEqual(result.name, "Combo")
        self.assertEqual(len(result.additionals), 1)
        self.product_repo.select_by_id.assert_awaited()

    async def test_update_offer_additionals(self):
        self.product_repo.select_by_id.return_value = await self._product_in_db()
        created = await self.service.create(await self._request_offer())
        self.product_repo.select_by_id.return_value = await self._product_in_db()
        update = UpdateOffer(
            name="New",
            additionals=[
                Additional(
                    name="Cheese",
                    unit_price=1.0,
                    unit_cost=0.5,
                    min_quantity=1,
                    max_quantity=3,
                )
            ],
            products=["p1"],
        )
        updated = await self.service.update(id=created.id, updated_offer=update)
        self.assertEqual(updated.name, "New")
        self.assertEqual(updated.additionals[0].name, "Cheese")

