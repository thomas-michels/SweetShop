from typing import List

from fastapi import APIRouter, Depends, Query, Security, Response

from app.api.composers import terms_of_use_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.shared_schemas.terms_of_use import FilterTermOfUse
from app.crud.users import UserInDB
from app.crud.terms_of_use import TermOfUseServices, TermOfUseInDB
from app.crud.users.schemas import CompleteUserInDB

router = APIRouter(tags=["Terms Of Use"])


@router.get("/terms_of_use", responses={200: {"model": List[TermOfUseInDB]}})
async def get_terms_of_use(
    filter: FilterTermOfUse = Query(default=FilterTermOfUse.ALL),
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=[]),
    terms_of_use_services: TermOfUseServices = Depends(terms_of_use_composer),
):
    terms_of_use = await terms_of_use_services.search_term_of_use_all(filter=filter)

    if terms_of_use:
        return build_response(
            status_code=200, message="Term of use found with success", data=terms_of_use
        )

    else:
        return Response(status_code=204)


@router.get("/terms_of_use/{terms_of_use_id}", responses={200: {"model": TermOfUseInDB}})
async def get_terms_of_use_by_id(
    terms_of_use_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=[]),
    terms_of_use_services: TermOfUseServices = Depends(terms_of_use_composer),
):
    terms_of_use_in_db = await terms_of_use_services.search_term_of_use_by_id(id=terms_of_use_id)

    if terms_of_use_in_db:
        return build_response(
            status_code=200, message="Term of use found with success", data=terms_of_use_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Term of use {terms_of_use_id} not found", data=None
        )


@router.get("/terms_of_use/{terms_of_use_id}/acceptance", responses={200: {"model": TermOfUseInDB}})
async def get_terms_of_use_acceptance_by_id(
    terms_of_use_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=[]),
    terms_of_use_services: TermOfUseServices = Depends(terms_of_use_composer),
):
    terms_of_use_in_db = await terms_of_use_services.search_acceptance_by_id(
        term_of_use_id=terms_of_use_id,
        user_id=current_user.user_id
    )

    if terms_of_use_in_db:
        return build_response(
            status_code=200, message="Term of use found with success", data=terms_of_use_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Term of use {terms_of_use_id} not found", data=None
        )
