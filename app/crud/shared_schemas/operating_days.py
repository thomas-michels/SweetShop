import re
from typing import List
from pydantic import Field, model_validator
from app.core.models.base_schema import GenericModel


class IntervalWork(GenericModel):
    start_work: str = Field(example="10:10")
    end_work: str = Field(example="12:00")

    @model_validator(mode="after")
    def validate_work_time(self) -> "IntervalWork":
        time_pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'

        if not re.match(time_pattern, self.start_work):
            raise ValueError(f"start_work '{self.start_work}' não está no formato hh:mm válido (00:00-23:59)")

        if not re.match(time_pattern, self.end_work):
            raise ValueError(f"end_work '{self.end_work}' não está no formato hh:mm válido (00:00-23:59)")

        return self


class OperatingDay(GenericModel):
    day: int = Field(example=5)
    intervals: List[IntervalWork] = Field(default=[])
