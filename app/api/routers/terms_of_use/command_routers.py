from fastapi import APIRouter, Depends, Form, Request, Security, UploadFile
from app.api.composers import terms_of_use_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.dependencies.auth import verify_super_user
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.terms_of_use import (
    TermOfUseAcceptance,
    TermOfUseAcceptanceInDB,
    TermOfUseInDB,
    TermOfUseServices,
)
from app.crud.users.schemas import CompleteUserInDB

router = APIRouter(tags=["Terms Of Use"])


@router.post("/terms_of_use", responses={201: {"model": TermOfUseInDB}})
async def create_term_of_use(
    file: UploadFile,
    version: str = Form(example="1.0.0"),
    term_of_use_services: TermOfUseServices = Depends(terms_of_use_composer),
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=[]),
):
    verify_super_user(current_user=current_user)

    term_of_use_in_db = await term_of_use_services.create_term_of_use(
        version=version, file=file
    )

    if term_of_use_in_db:
        return build_response(
            status_code=201,
            message="Term Of Use created with success",
            data=term_of_use_in_db,
        )

    else:
        return build_response(
            status_code=400,
            message="Some error happened on create a term of use",
            data=None,
        )


@router.delete(
    "/terms_of_use/{term_of_use_id}", responses={200: {"model": TermOfUseInDB}}
)
async def delete_term_of_use(
    term_of_use_id: str,
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=[]),
    term_of_use_services: TermOfUseServices = Depends(terms_of_use_composer),
):
    verify_super_user(current_user=current_user)

    term_of_use_in_db = await term_of_use_services.delete_term_of_use_by_id(
        id=term_of_use_id
    )

    if term_of_use_in_db:
        return build_response(
            status_code=200,
            message="Term Of Use deleted with success",
            data=term_of_use_in_db,
        )

    else:
        return build_response(
            status_code=404,
            message=f"Term Of Use {term_of_use_id} not found",
            data=None,
        )


@router.post(
    "/terms_of_use/{term_of_use_id}/accept",
    responses={200: {"model": TermOfUseAcceptanceInDB}},
)
async def accepted_term_of_use(
    request: Request,
    term_of_use_id: str,
    term_of_use_services: TermOfUseServices = Depends(terms_of_use_composer),
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=[]),
):
    now = UTCDateTime.now().timestamp()

    client_ip = request.headers.get("fly-client-ip")

    acceptance = TermOfUseAcceptance(
        term_of_use_id=term_of_use_id,
        user_id=current_user.user_id,
        acceptance_method="checkbox",
        accepted_at=now,
        ip_address=client_ip if client_ip else "unknown",
        user_agent=request.headers.get("User-Agent", "unknown"),
    )

    term_of_use_in_db = await term_of_use_services.accept_term_of_use(
        acceptance=acceptance
    )

    if term_of_use_in_db:
        return build_response(
            status_code=200,
            message="Term Of Use accepted with success",
            data=term_of_use_in_db,
        )

    else:
        return build_response(
            status_code=400,
            message="Some error happened on accept a term of use",
            data=None,
        )


@router.delete(
    "/terms_of_use/{term_of_use_id}/reject",
    responses={200: {"model": TermOfUseAcceptanceInDB}},
)
async def delete_term_of_use(
    term_of_use_id: str,
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=[]),
    term_of_use_services: TermOfUseServices = Depends(terms_of_use_composer),
):
    verify_super_user(current_user=current_user)

    term_of_use_in_db = await term_of_use_services.delete_acceptance(
        term_of_use_id=term_of_use_id, user_id=current_user.user_id
    )

    if term_of_use_in_db:
        return build_response(
            status_code=200,
            message="Term Of Use rejected with success",
            data=term_of_use_in_db,
        )

    else:
        return build_response(
            status_code=404,
            message=f"Term Of Use {term_of_use_id} not found",
            data=None,
        )
