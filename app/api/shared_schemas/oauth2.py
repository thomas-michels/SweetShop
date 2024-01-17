from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/signin",
    scopes={
        "user:me": "Read information about the current user.",
        "user:get": "Read information about users.",
        "user:update": "Update information about users.",
        "user:delete": "Delete information about users.",
    },
)
