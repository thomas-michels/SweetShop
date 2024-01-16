from fastapi.security import (
    OAuth2PasswordBearer,
    SecurityScopes,
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/signin",
    scopes={"me": "Read information about the current user.", "items": "Read items."},
)
