from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.core.utils import slugify


@pytest.mark.parametrize(
    "raw, expected",
    (
        ("Café da manhã", "cafe-da-manha"),
        ("   spaces   everywhere   ", "spaces-everywhere"),
        ("already-a-slug", "already-a-slug"),
        ("with/special\\chars", "withspecialchars"),
        ("", ""),
    ),
)
def test_slugify_returns_normalized_slug(raw: str, expected: str) -> None:
    assert slugify(raw) == expected


def test_slugify_raises_type_error_for_non_strings() -> None:
    with pytest.raises(TypeError):
        slugify(None)  # type: ignore[arg-type]
