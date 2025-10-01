"""Utility helpers for slug generation."""

import re
import unicodedata


def slugify(value: str) -> str:
    """Return a URL friendly representation of ``value``.

    The function removes accentuation and non alphanumeric characters while
    converting blank spaces to hyphens. The resulting slug is normalized to
    lower case to avoid duplicated values caused by different casing.
    """

    if not isinstance(value, str):  # pragma: no cover - defensive programming
        msg = "slugify expects a string value"
        raise TypeError(msg)

    if not value:
        return ""

    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_value = ascii_value.replace("_", " ")
    cleaned = re.sub(r"[^A-Za-z0-9\s-]", "", ascii_value)
    collapsed = re.sub(r"[\s-]+", "-", cleaned).strip("-")

    return collapsed.lower()


__all__ = ["slugify"]
