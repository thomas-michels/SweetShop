from datetime import datetime
from mongoengine import StringField, DictField, BooleanField, IntField
from app.core.models.base_document import BaseDocument


class TermOfUseModel(BaseDocument):
    version = StringField(required=True, unique=True)
    hash = StringField(required=True, unique=True)
    url = StringField(required=True, unique=True)

    meta = {"collection": "terms_of_use"}

    def update(self, **kwargs):
        self.base_update()
        if kwargs.get("updated_at"):
            kwargs.pop("updated_at")
            return super().update(updated_at=self.updated_at,**kwargs)

        return super().update(updated_at=datetime.now(), **kwargs)

    def delete(self, soft_delete: bool = True, signal_kwargs=None, **write_concern):
        if soft_delete:
            self.soft_delete()
            self.save()

        else:
            return super().delete(signal_kwargs, **write_concern)


class TermOfUseAcceptanceModel(BaseDocument):
    term_of_use_id = StringField(required=True)  # Qual termo foi aceito
    user_id = StringField(required=True)  # Quem aceitou
    accepted_at = IntField(required=True)  # Data e hora da aceitação
    ip_address = StringField(required=False)  # Endereço IP do usuário
    user_agent = StringField(required=False)  # Informações sobre o dispositivo/navegador
    acceptance_method = StringField(required=False)  # Método de aceitação

    lgpd_consent = BooleanField(required=True, default=True)  # Confirmação de consentimento
    lgpd_purpose = StringField(required=True, default="Aceitação dos Termos de Uso")  # Finalidade do tratamento
    lgpd_data_retention = StringField(
        required=True,
        default="Até a revogação do consentimento ou conforme obrigação legal"
    )  # Política de retenção de dados

    extra_data = DictField(default={})  # Possíveis informações adicionais

    meta = {
        "collection": "terms_of_use_acceptance",
        "indexes": [
            ("term_of_use_id", "user_id"),  # Index para buscas rápidas
        ],
    }

    def update(self, **kwargs):
        self.base_update()
        if kwargs.get("updated_at"):
            kwargs.pop("updated_at")
            return super().update(updated_at=self.updated_at,**kwargs)

        return super().update(updated_at=datetime.now(), **kwargs)

    def delete(self, soft_delete: bool = True, signal_kwargs=None, **write_concern):
        if soft_delete:
            self.soft_delete()
            self.save()

        else:
            return super().delete(signal_kwargs, **write_concern)
