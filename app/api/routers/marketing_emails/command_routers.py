from fastapi import APIRouter, Depends

from app.api.composers import marketing_email_composer
from app.api.dependencies import build_response
from app.crud.marketing_emails import (
    MarketingEmail,
    MarketingEmailInDB,
    MarketingEmailServices
)

router = APIRouter(tags=["Marketing Emails"])


@router.post("/marketing_emails", responses={201: {"model": MarketingEmailInDB}})
async def collect_marketing_email(
    marketing_email: MarketingEmail,
    marketing_email_services: MarketingEmailServices = Depends(marketing_email_composer),
):
    marketing_email_in_db = await marketing_email_services.create(marketing_email=marketing_email)

    if marketing_email_in_db:
        return build_response(
            status_code=201, message="MarketingEmail created with success", data=marketing_email_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on create a marketing_email", data=None
        )
