"""Shared dependencies for FastAPI routers.

This package re-exports common dependency callables.  Importing the
authentication helpers at module import time can lead to circular import
issues, so :func:`decode_jwt` is loaded lazily via ``__getattr__``.  This keeps
the public API backwards compatible while avoiding import cycles.
"""

from .response import build_response

__all__ = ["build_response", "decode_jwt"]


def __getattr__(name: str):  # pragma: no cover - simple delegation
    if name == "decode_jwt":
        from .auth import decode_jwt  # imported lazily to avoid circular import

        return decode_jwt
    raise AttributeError(f"module 'app.api.dependencies' has no attribute {name!r}")

