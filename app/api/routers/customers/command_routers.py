from fastapi import APIRouter, Depends, Security

from app.api.composers import customer_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.customers import (
    Customer,
    CustomerInDB,
    UpdateCustomer,
    CustomerServices
)
from app.crud.users import UserInDB

router = APIRouter(tags=["Customers"])


@router.post("/customers", responses={201: {"model": CustomerInDB}})
async def create_customer(
    customer: Customer,
    customer_services: CustomerServices = Depends(customer_composer),
    current_user: UserInDB = Security(decode_jwt, scopes=["customer:create"]),
):
    customer_in_db = await customer_services.create(customer=customer)

    if customer_in_db:
        return build_response(
            status_code=201, message="Customer created with success", data=customer_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on create a customer", data=None
        )


@router.put("/customers/{customer_id}", responses={200: {"model": CustomerInDB}})
async def update_customer(
    customer_id: str,
    customer: UpdateCustomer,
    current_user: UserInDB = Security(decode_jwt, scopes=["customer:create"]),
    customer_services: CustomerServices = Depends(customer_composer),
):
    customer_in_db = await customer_services.update(id=customer_id, updated_customer=customer)

    if customer_in_db:
        return build_response(
            status_code=200, message="Customer updated with success", data=customer_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on update a customer", data=None
        )


@router.delete("/customers/{customer_id}", responses={200: {"model": CustomerInDB}})
async def delete_customer(
    customer_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["customer:create"]),
    customer_services: CustomerServices = Depends(customer_composer),
):
    customer_in_db = await customer_services.delete_by_id(id=customer_id)

    if customer_in_db:
        return build_response(
            status_code=200, message="Customer deleted with success", data=customer_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Customer {customer_id} not found", data=None
        )
