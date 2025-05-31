from pydantic import Field

from app.core.models.base_model import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.core.utils.utc_datetime import UTCDateTime


class TermOfUse(GenericModel):
    version: str = Field(example="1.0.0")
    hash: str = Field(example="234asd")
    url: str = Field(example="234asd")


class TermOfUseInDB(TermOfUse, DatabaseModel):
    hash: str = Field(example="234asd", exclude=True)


class TermOfUseAcceptance(GenericModel):
    term_of_use_id: str = Field(example="ter_123")
    user_id: str = Field(example="user_123")
    accepted_at: float = Field(example=str(UTCDateTime.now().timestamp()))
    ip_address: str = Field(example="192.168.0.1")
    user_agent: str = Field(example="Google Chrome")
    acceptance_method: str = Field(example="button")
    lgpd_consent: bool = Field(default=True, example=True)
    lgpd_purpose: str = Field(default="Aceitação dos Termos de Uso", example="Terms")
    lgpd_data_retention: str = Field(
        default="Até a revogação do consentimento ou conforme obrigação legal",
        example="Terms",
    )
    extra_data: dict = Field(default={})


class TermOfUseAcceptanceInDB(TermOfUseAcceptance, DatabaseModel): ...
