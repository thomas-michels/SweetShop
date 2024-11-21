from authlib.integrations.starlette_client import OAuth
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.api.dependencies.response import build_response
from app.api.routers import (
    user_router,
    product_router,
    authentication_router,
    order_router,
    customer_router,
    tag_router
)
from app.api.routers.exception_handlers import (
    unprocessable_entity_error_422,
    generic_error_500,
    not_found_error_404,
    generic_error_400,
)
from app.api.shared_schemas.token import Token
from app.core.db.connection import lifespan
from app.core.exceptions import UnprocessableEntity, NotFoundError, InvalidPassword
from app.core.configs import get_environment

_env = get_environment()


app = FastAPI(title=_env.APPLICATION_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=_env.APP_SECRET_KEY)

app.include_router(authentication_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(product_router, prefix="/api")
app.include_router(order_router, prefix="/api")
app.include_router(customer_router, prefix="/api")
app.include_router(tag_router, prefix="/api")

app.add_exception_handler(UnprocessableEntity, unprocessable_entity_error_422)
app.add_exception_handler(NotFoundError, not_found_error_404)
app.add_exception_handler(InvalidPassword, generic_error_400)
app.add_exception_handler(Exception, generic_error_500)


oauth = OAuth()
oauth.register(
    "auth0",
    client_id=_env.AUTH0_CLIENT_ID,
    client_secret=_env.AUTH0_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f"{_env.AUTH0_DOMAIN}/.well-known/openid-configuration"
)


@app.get("/login", tags=["Login"])
async def login(request: Request):
    return await oauth.auth0.authorize_redirect(
        request=request,
        redirect_uri=request.url_for("callback")
    )


@app.route("/callback", methods=["GET", "POST"])
async def callback(request: Request):
    token = await oauth.auth0.authorize_access_token(request=request)

    if token:
        return build_response(
            status_code=200, message="Login successed!", data=Token(
                access_token=token["id_token"],
                expires_in=token["expires_in"],
                token_type=token["token_type"]
            )
        )

    else:
        return build_response(status_code=403, message="Unauthorized!", data=None)


@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"message": "I'm alive"}
