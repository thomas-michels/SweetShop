from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.core.utils.features import Feature, get_translation


@pytest.mark.parametrize(
    "feature, expected",
    (
        (Feature.MAX_USERS, "Usuários"),
        (Feature.MAX_PRODUCTS, "Produtos"),
        (Feature.DISPLAY_DASHBOARD, "Painel financeiro"),
        (Feature.SUPPORT, "Suporte via WhatsApp"),
    ),
)
def test_get_translation_returns_expected_label(feature: Feature, expected: str) -> None:
    assert get_translation(feature) == expected


@pytest.mark.parametrize(
    "raw, expected",
    (
        ("-", "Ilimitado"),
        ("true", "Incluído"),
        ("false", "Não incluído"),
    ),
)
def test_get_translation_handles_special_string_values(raw: str, expected: str) -> None:
    assert get_translation(raw) == expected


def test_get_translation_returns_none_for_unknown_feature() -> None:
    assert get_translation("UNKNOWN") is None
