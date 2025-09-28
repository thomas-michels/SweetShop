from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.core.utils.validate_document import validate_cpf, validate_cnpj


@pytest.mark.parametrize(
    "cpf, expected",
    (
        ("52998224725", True),
        ("12345678909", True),
        ("00000000000", False),
        ("52998224724", False),
        ("123", False),
    ),
)
def test_validate_cpf(cpf: str, expected: bool) -> None:
    assert validate_cpf(cpf) is expected


@pytest.mark.parametrize(
    "cnpj, expected",
    (
        ("11444777000161", True),
        ("04252011000110", True),
        ("00000000000000", False),
        ("11444777000160", False),
        ("123456789012", False),
    ),
)
def test_validate_cnpj(cnpj: str, expected: bool) -> None:
    assert validate_cnpj(cnpj) is expected
