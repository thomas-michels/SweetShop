from datetime import datetime
from pathlib import Path
import sys

import pytest
import pytz
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.core.utils.utc_datetime import UTCDateTime, UTCDateTimeType


def test_utc_datetime_defaults_to_utc() -> None:
    dt = UTCDateTime(2024, 1, 1, 12, 30, 15)

    assert dt.tzinfo is pytz.UTC
    assert str(dt).endswith("Z")


def test_utc_datetime_converts_from_aware_timezone() -> None:
    eastern = pytz.timezone("US/Eastern")
    aware = eastern.localize(datetime(2024, 1, 1, 7, 30, 15))

    converted = UTCDateTime(
        aware.year,
        aware.month,
        aware.day,
        aware.hour,
        aware.minute,
        aware.second,
        aware.microsecond,
        tzinfo=aware.tzinfo,
    )

    assert converted.tzinfo is pytz.UTC
    assert converted.hour == 12
    assert converted.minute == 30


def test_utc_datetime_timestamp_returns_integer() -> None:
    dt = UTCDateTime(1970, 1, 1, 0, 0, 5)

    assert dt.timestamp() == 5


@pytest.mark.parametrize(
    "value",
    (
        "2024-01-01T12:00:00Z",
        "2024-01-01T09:00:00-03:00",
        "2024-01-01T12:00:00",
        datetime(2024, 1, 1, 12, 0, 0),
        pytz.timezone("US/Pacific").localize(datetime(2024, 1, 1, 4, 0, 0)),
    ),
)
def test_validate_datetime_accepts_multiple_formats(value) -> None:
    parsed = UTCDateTime.validate_datetime(value)

    assert isinstance(parsed, UTCDateTime)
    assert parsed.tzinfo is pytz.UTC


def test_validate_datetime_raises_value_error_for_invalid_input() -> None:
    with pytest.raises(ValueError):
        UTCDateTime.validate_datetime(42)


class _UTCModel(BaseModel):
    timestamp: UTCDateTimeType


def test_utc_datetime_type_integrates_with_pydantic() -> None:
    model = _UTCModel(timestamp="2024-01-01T12:00:00Z")

    assert isinstance(model.timestamp, UTCDateTime)
    assert model.model_dump()["timestamp"].tzinfo is pytz.UTC
