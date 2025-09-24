from asgi_correlation_id import CorrelationIdMiddleware
import sentry_sdk
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.dependencies.get_access_token import get_access_token
from app.api.dependencies.response import build_response
from app.api.dependencies.whats_app_adapter import WhatsAppMessageSender
from app.api.middleware.rate_limiting import RateLimitMiddleware
from app.api.routers import (
    user_router,
    product_router,
    order_router,
    customer_router,
    tag_router,
    organization_router,
    billing_router,
    fast_order_router,
    expenses_router,
    invite_router,
    payment_router,
    organization_plan_router,
    plan_router,
    plan_feature_router,
    mercado_pago_router,
    subscription_router,
    coupon_router,
    marketing_email_router,
    calendar_router,
    term_of_use_router,
    file_router,
    section_router,
    section_item_router,
    menu_router,
    offer_router,
    home_router,
    pre_order_router,
    message_router,
    additional_router,
    business_day_router
)
from app.api.routers.exception_handlers import (
    unprocessable_entity_error_422,
    generic_error_500,
    not_found_error_404,
    generic_error_400,
)
from app.api.routers.exception_handlers.generic_errors import http_exception_handler
from app.core.db.connection import lifespan
from app.core.exceptions import UnprocessableEntity, NotFoundError, InvalidPassword
from app.core.configs import get_environment

_env = get_environment()


sentry_sdk.init(
    dsn=_env.SENTRY_DSN,
    traces_sample_rate=1.0,
    server_name=_env.APPLICATION_NAME,
    release=_env.RELEASE,
    environment=_env.ENVIRONMENT,
    enable_logs=True,
    _experiments={
        "continuous_profiling_auto_start": True,
    },
)


app = FastAPI(
    title=_env.APPLICATION_NAME,
    lifespan=lifespan,
    version=_env.RELEASE
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(RateLimitMiddleware, limit=250, window=60)

app.include_router(organization_router, prefix="/api")
app.include_router(organization_plan_router, prefix="/api")
app.include_router(invite_router, prefix="/api")
app.include_router(subscription_router, prefix="/api")
app.include_router(plan_router, prefix="/api")
app.include_router(plan_feature_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(term_of_use_router, prefix="/api")
app.include_router(product_router, prefix="/api")
app.include_router(additional_router, prefix="/api")
app.include_router(order_router, prefix="/api")
app.include_router(pre_order_router, prefix="/api")
app.include_router(payment_router, prefix="/api")
app.include_router(fast_order_router, prefix="/api")
app.include_router(menu_router, prefix="/api")
app.include_router(section_router, prefix="/api")
app.include_router(section_item_router, prefix="/api")
app.include_router(offer_router, prefix="/api")
app.include_router(billing_router, prefix="/api")
app.include_router(home_router, prefix="/api")
app.include_router(calendar_router, prefix="/api")
app.include_router(customer_router, prefix="/api")
app.include_router(tag_router, prefix="/api")
app.include_router(expenses_router, prefix="/api")
app.include_router(coupon_router, prefix="/api")
app.include_router(file_router, prefix="/api")
app.include_router(marketing_email_router, prefix="/api")
app.include_router(message_router, prefix="/api")
app.include_router(mercado_pago_router, prefix="/api")
app.include_router(business_day_router, prefix="/api")

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(UnprocessableEntity, unprocessable_entity_error_422)
app.add_exception_handler(NotFoundError, not_found_error_404)
app.add_exception_handler(InvalidPassword, generic_error_400)
app.add_exception_handler(Exception, generic_error_500)


@app.get("/")
async def root_path(request: Request):
    return build_response(status_code=200, message="I'm alive!", data=None)


@app.get("/health", tags=["Health Check"])
async def health_check(
    access_token=Depends(get_access_token),
):
    wa = WhatsAppMessageSender()

    if access_token and wa.check_whatsapp_numbers(number="5547996240277"):
        return build_response(status_code=200, message="I'm alive!", data=None)

    return build_response(status_code=400, message="Health check failed", data=None)


@app.head("/health", tags=["Health Check"])
async def monitor_health_check(
    access_token=Depends(get_access_token),
):
    wa = WhatsAppMessageSender()

    if access_token and wa.check_whatsapp_numbers(number="5547996240277"):
        return build_response(status_code=200, message="I'm alive!", data=None)

    return build_response(status_code=400, message="Health check failed", data=None)
