from typing import List

from pydantic import Field, ConfigDict

from app.api.shared_schemas.responses import Response, ListResponseSchema
from app.crud.customers.schemas import CustomerInDB

EXAMPLE_CUSTOMER = {
    "id": "cus_123",
    "name": "John Doe",
    "international_code": "55",
    "ddd": "047",
    "phone_number": "999999999",
    "document": "11155521999",
    "addresses": [],
    "tags": ["vip"],
    "date_of_birth": "2024-01-01T00:00:00Z",
    "email": "john@example.com",
    "organization_id": "org_123",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}


class GetCustomerResponse(Response):
    data: CustomerInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Cliente encontrado",
                "data": EXAMPLE_CUSTOMER,
            }
        }
    )


class GetCustomersResponse(ListResponseSchema):
    data: List[CustomerInDB] = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Clientes encontrados com sucesso",
                "pagination": {"page": 1, "page_size": 2, "total": 2},
                "data": [
                    EXAMPLE_CUSTOMER,
                    {**EXAMPLE_CUSTOMER, "id": "cus_456", "email": "other@example.com"},
                ],
            }
        }
    )


class GetCustomersCountResponse(Response):
    data: int | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Contagem de clientes feita com sucesso",
                "data": 2,
            }
        }
    )


class CreateCustomerResponse(Response):
    data: CustomerInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Cliente criado com sucesso",
                "data": EXAMPLE_CUSTOMER,
            }
        }
    )


class UpdateCustomerResponse(Response):
    data: CustomerInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Cliente atualizado com sucesso",
                "data": EXAMPLE_CUSTOMER,
            }
        }
    )


class DeleteCustomerResponse(Response):
    data: CustomerInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Cliente deletado com sucesso",
                "data": EXAMPLE_CUSTOMER,
            }
        }
    )
