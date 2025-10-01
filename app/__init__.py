"""Application package."""

# The FastAPI application instance lives in :mod:`app.application`.
# Importing it at package import time can pull in many optional
# dependencies during test collection, so it is intentionally left
# out of the top-level namespace here.  Accessing ``api_app`` will
# load it lazily when required by the application runtime.

__all__ = ["api_app"]


def __getattr__(name: str):
    if name == "api_app":
        from .application import app as api_app

        return api_app
    raise AttributeError(name)
