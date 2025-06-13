import os

ENV_VARS = {
    "AUTH0_DOMAIN": "test",
    "AUTH0_API_AUDIENCE": "test",
    "AUTH0_ISSUER": "test",
    "AUTH0_ALGORITHMS": "HS256",
    "AUTH0_CLIENT_ID": "test",
    "AUTH0_CLIENT_SECRET": "test",
    "APP_SECRET_KEY": "test",
    "AUTH0_MANAGEMENT_API_CLIENT_ID": "test",
    "AUTH0_MANAGEMENT_API_CLIENT_SECRET": "test",
    "AUTH0_MANAGEMENT_API_AUDIENCE": "test",
}

for key, value in ENV_VARS.items():
    os.environ.setdefault(key, value)
