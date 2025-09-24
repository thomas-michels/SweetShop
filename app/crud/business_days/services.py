from typing import Optional

from .repositories import BusinessDayRepository
from .schemas import BusinessDayInDB, UpsertBusinessDay


class BusinessDayServices:
    def __init__(self, business_day_repository: BusinessDayRepository) -> None:
        self._business_day_repository = business_day_repository

    async def upsert_today(self, business_day: UpsertBusinessDay) -> Optional[BusinessDayInDB]:
        return await self._business_day_repository.upsert_today(
            menu_id=business_day.menu_id,
            closes_at=business_day.closes_at,
        )

    async def get_today(self) -> Optional[BusinessDayInDB]:
        return await self._business_day_repository.select_today()
