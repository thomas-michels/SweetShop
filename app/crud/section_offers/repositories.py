from typing import List

from pydantic import ValidationError

from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository
from app.core.utils.utc_datetime import UTCDateTime

from .models import SectionOfferModel
from .schemas import SectionOffer, SectionOfferInDB

_logger = get_logger(__name__)


class SectionOfferRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.organization_id = organization_id

    async def create(self, section_offer: SectionOffer) -> SectionOfferInDB:
        try:
            model = SectionOfferModel(
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
                organization_id=self.organization_id,
                **section_offer.model_dump(),
            )

            model.save()
            return SectionOfferInDB.model_validate(model)

        except Exception as error:
            _logger.error(f"Error on create_section_offer: {error}")
            raise UnprocessableEntity(message="Error on create new section offer")

    async def update(self, section_offer: SectionOfferInDB) -> SectionOfferInDB:
        try:
            model: SectionOfferModel = SectionOfferModel.objects(
                id=section_offer.id, is_active=True, organization_id=self.organization_id
            ).first()

            model.update(**section_offer.model_dump())

            return await self.select_by_id(id=section_offer.id)

        except ValidationError:
            raise NotFoundError(message="Section offer not found")

        except Exception as error:
            _logger.error(f"Error on update_section_offer: {error}")
            raise UnprocessableEntity(message="Error on update section offer")

    async def select_by_id(self, id: str, raise_404: bool = True) -> SectionOfferInDB:
        try:
            model: SectionOfferModel = SectionOfferModel.objects(
                id=id, is_active=True, organization_id=self.organization_id
            ).first()
            return SectionOfferInDB.model_validate(model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {error}")
            if raise_404:
                raise NotFoundError(message=f"SectionOffer #{id} not found")

    async def select_all(self, section_id: str, is_visible: bool = None) -> List[SectionOfferInDB]:
        try:
            results = []

            objects = SectionOfferModel.objects(
                is_active=True, organization_id=self.organization_id, section_id=section_id
            )

            if is_visible is not None:
                objects = objects.filter(is_visible=is_visible)

            for model in objects.order_by("position"):
                results.append(SectionOfferInDB.model_validate(model))

            return results

        except Exception as error:
            _logger.error(f"Error on select_all: {error}")
            raise NotFoundError(message="Section offers not found")

    async def delete_by_id(self, id: str) -> SectionOfferInDB:
        try:
            model: SectionOfferModel = SectionOfferModel.objects(
                id=id, is_active=True, organization_id=self.organization_id
            ).first()

            if model:
                model.delete()
                return SectionOfferInDB.model_validate(model)

            raise NotFoundError(message=f"SectionOffer #{id} not found")

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {error}")
            raise NotFoundError(message=f"SectionOffer #{id} not found")
