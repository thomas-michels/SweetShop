from typing import List
from pydantic import ValidationError
from mongoengine.queryset.visitor import Q

from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository
from app.core.utils.utc_datetime import UTCDateTime

from .models import OfferModel
from .schemas import Offer, OfferInDB

_logger = get_logger(__name__)


class OfferRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.organization_id = organization_id

    async def create(self, offer: Offer) -> OfferInDB:
        try:
            offer_model = OfferModel(
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
                organization_id=self.organization_id,
                **offer.model_dump(),
            )
            offer_model.name = offer_model.name.title()

            offer_model.save()
            _logger.info(
                f"Offer {offer.name} saved for organization {self.organization_id}"
            )

            return OfferInDB.model_validate(offer_model)

        except Exception as error:
            _logger.error(f"Error on create_offer: {error}")
            raise UnprocessableEntity(message="Error on create new offer")

    async def update(self, offer: OfferInDB) -> OfferInDB:
        try:
            offer_model: OfferModel = OfferModel.objects(
                id=offer.id, is_active=True, organization_id=self.organization_id
            ).first()
            offer.name = offer.name.title()

            offer_model.update(**offer.model_dump())

            return await self.select_by_id(id=offer.id)

        except ValidationError:
            raise NotFoundError(message=f"Offer not found")

        except Exception as error:
            _logger.error(f"Error on update_offer: {error}")
            raise UnprocessableEntity(message="Error on update offer")

    async def select_by_id(self, id: str, raise_404: bool = True) -> OfferInDB:
        try:
            offer_model: OfferModel = OfferModel.objects(
                id=id, is_active=True, organization_id=self.organization_id
            ).first()

            return OfferInDB.model_validate(offer_model)

        except ValidationError:
            if raise_404:
                raise NotFoundError(message=f"Offer #{id} not found")

        except Exception as error:
            _logger.error(f"Error on select_by_id: {error}")
            if raise_404:
                raise NotFoundError(message=f"Offer #{id} not found")

    async def select_all(
        self, section_id: str, is_visible: bool = None
    ) -> List[OfferInDB]:
        try:
            offers = []

            objects = OfferModel.objects(
                is_active=True,
                organization_id=self.organization_id,
                section_id=section_id,
            )

            if is_visible is not None:
                objects = objects.filter(is_visible=is_visible)

            for offer_model in objects.order_by("position"):
                offers.append(OfferInDB.model_validate(offer_model))

            return offers

        except Exception as error:
            _logger.error(f"Error on select_all: {error}")
            raise NotFoundError(message=f"Offers not found")

    async def select_count(self, query: str = None, is_visible: bool = None) -> int:
        try:
            objects = OfferModel.objects(
                is_active=True,
                organization_id=self.organization_id,
            )

            now = UTCDateTime.now()
            objects = objects.filter(
                (Q(starts_at__lte=now) | Q(starts_at=None))
                & (Q(ends_at__gte=now) | Q(ends_at=None))
            )

            if query:
                objects = objects.filter(name__iregex=query)

            if is_visible is not None:
                objects = objects.filter(is_visible=is_visible)

            return max(objects.count(), 0)

        except Exception as error:
            _logger.error(f"Error on select_count: {error}")
            return 0

    async def select_all_paginated(
        self,
        query: str = None,
        page: int = None,
        page_size: int = None,
        is_visible: bool = None,
    ) -> List[OfferInDB]:
        try:
            offers = []

            objects = OfferModel.objects(
                is_active=True,
                organization_id=self.organization_id,
            )

            now = UTCDateTime.now()
            objects = objects.filter(
                (Q(starts_at__lte=now) | Q(starts_at=None))
                & (Q(ends_at__gte=now) | Q(ends_at=None))
            )

            if query:
                objects = objects.filter(name__iregex=query)

            if is_visible is not None:
                objects = objects.filter(is_visible=is_visible)

            if page is not None and page_size is not None:
                skip = (page - 1) * page_size
                objects = objects.order_by("name").skip(skip).limit(page_size)
            else:
                objects = objects.order_by("name")

            for offer_model in objects:
                offers.append(OfferInDB.model_validate(offer_model))

            return offers

        except Exception as error:
            _logger.error(f"Error on select_all_paginated: {error}")
            raise NotFoundError(message=f"Offers not found")

    async def select_all_by_product_id(self, product_id: str) -> List[OfferInDB]:
        try:
            offers = []

            objects = OfferModel.objects(
                is_active=True,
                organization_id=self.organization_id,
            )

            for offer_model in objects:
                for product in offer_model.products:
                    if product.get("product_id") == product_id:
                        try:
                            offer = OfferInDB.model_validate(offer_model)

                        except Exception:
                            continue

                        offers.append(offer)
                        break

            return offers

        except Exception as error:
            _logger.error(f"Error on select_all_by_product_id: {error}")
            raise NotFoundError(message=f"Offers not found")

    async def delete_by_id(self, id: str) -> OfferInDB:
        try:
            offer_model: OfferModel = OfferModel.objects(
                id=id, is_active=True, organization_id=self.organization_id
            ).first()

            if offer_model:
                offer_model.delete()

                return OfferInDB.model_validate(offer_model)

            raise NotFoundError(message=f"Offer #{id} not found")

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {error}")
            raise NotFoundError(message=f"Offer #{id} not found")
