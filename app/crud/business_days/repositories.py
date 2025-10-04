from datetime import timedelta
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

    def _recent_active_query(self, menu_id: str, now: UTCDateTime | None = None):
        reference = now or UTCDateTime.now()
        window_start = reference - timedelta(hours=24)
        window_end = reference + timedelta(hours=24)

        return (
            BusinessDayModel.objects(
                organization_id=self.organization_id,
                menu_id=menu_id,
                is_active=True,
                closes_at__gte=window_start,
                closes_at__lte=window_end,
            )
            .order_by("-closes_at")
        )

    async def upsert_today(self, menu_id: str, closes_at: UTCDateTime) -> Optional[BusinessDayInDB]:
        try:
            closes_at_utc = UTCDateTime.validate_datetime(closes_at)
            now = UTCDateTime.now()

            if closes_at_utc - now > timedelta(days=1):
                return None

            business_day: BusinessDayModel | None = self._recent_active_query(
                now=now,
                menu_id=menu_id
            ).first()

            day_value = now.strftime("%Y-%m-%d")

            if business_day:
                business_day.update(
                    menu_id=menu_id,
                    closes_at=closes_at_utc,
                    day=day_value,
                )
                business_day.reload()
            else:
                business_day = BusinessDayModel(
                    menu_id=menu_id,
                    organization_id=self.organization_id,
                    day=day_value,
                    closes_at=closes_at_utc,
                )
                business_day.save()

            return BusinessDayInDB.model_validate(business_day)
        except Exception as error:
            _logger.error(f"Error on upsert business day: {str(error)}")

    async def select_today(self, menu_id: str) -> Optional[BusinessDayInDB]:
        try:
            business_day: BusinessDayModel | None = self._recent_active_query(menu_id=menu_id).first()

            if not business_day:
                return None

            return BusinessDayInDB.model_validate(business_day)
        except Exception as error:
            _logger.error(f"Error on select business day: {str(error)}")
