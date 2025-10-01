from typing import Optional

from app.core.configs import get_logger
from app.core.repositories.base_repository import Repository
from app.core.utils.utc_datetime import UTCDateTime

from .models import BusinessDayModel
from .schemas import BusinessDayInDB

_logger = get_logger(__name__)


class BusinessDayRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.organization_id = organization_id

    def _today_key(self) -> dict:
        return {
            "organization_id": self.organization_id,
            "day": UTCDateTime.now().strftime("%Y-%m-%d"),
            "is_active": True,
        }

    async def upsert_today(self, menu_id: str, closes_at: UTCDateTime) -> Optional[BusinessDayInDB]:
        try:
            closes_at_utc = UTCDateTime.validate_datetime(closes_at)
            today_filter = self._today_key()

            business_day: BusinessDayModel | None = BusinessDayModel.objects(
                **today_filter
            ).first()

            if business_day:
                business_day.update(menu_id=menu_id, closes_at=closes_at_utc)
                business_day.reload()
            else:
                business_day = BusinessDayModel(
                    menu_id=menu_id,
                    organization_id=self.organization_id,
                    day=today_filter["day"],
                    closes_at=closes_at_utc,
                )
                business_day.save()

            return BusinessDayInDB.model_validate(business_day)
        except Exception as error:
            _logger.error(f"Error on upsert business day: {str(error)}")

    async def select_today(self) -> Optional[BusinessDayInDB]:
        try:
            business_day: BusinessDayModel | None = BusinessDayModel.objects(
                **self._today_key()
            ).first()

            if not business_day:
                return None

            return BusinessDayInDB.model_validate(business_day)
        except Exception as error:
            _logger.error(f"Error on select business day: {str(error)}")
