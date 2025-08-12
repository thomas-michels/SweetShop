from .response import build_response


async def decode_jwt(*args, **kwargs):
    """Lazily import and execute the ``decode_jwt`` dependency.

    Importing :mod:`app.api.dependencies.auth` at module load time creates a
    circular import when services import modules from this package.  Deferring
    the import until the function is called avoids the cycle while keeping the
    public API the same for the rest of the application and tests.
    """

    from .auth import decode_jwt as _decode_jwt

    return await _decode_jwt(*args, **kwargs)

