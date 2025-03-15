from app.crud.terms_of_use.term_of_use_repositories import TermOfUseRepository
from app.crud.terms_of_use.term_of_use_acceptance_repositories import TermOfUseAcceptanceRepository
from app.crud.terms_of_use.services import TermOfUseServices


async def terms_of_use_composer(
) -> TermOfUseServices:
    term_of_use_repository = TermOfUseRepository()
    acceptance_repository = TermOfUseAcceptanceRepository()

    terms_of_use_services = TermOfUseServices(
        term_of_use_repository=term_of_use_repository,
        acceptance_repository=acceptance_repository
    )
    return terms_of_use_services
