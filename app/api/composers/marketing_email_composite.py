from app.crud.marketing_emails.repositories import MarketingEmailRepository
from app.crud.marketing_emails.services import MarketingEmailServices


async def marketing_email_composer(
) -> MarketingEmailServices:
    marketing_email_repository = MarketingEmailRepository()
    marketing_email_services = MarketingEmailServices(marketing_email_repository=marketing_email_repository)
    return marketing_email_services
