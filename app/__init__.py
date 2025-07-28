"""Initialize the FastAPI application if dependencies are available."""

try:  # pragma: no cover - optional for tests
    from .application import app as api_app
except Exception:  # pragma: no cover - ignore missing optional deps during tests
    api_app = None
