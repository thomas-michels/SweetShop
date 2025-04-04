from fastapi import APIRouter, Depends, Response, Security

from app.api.composers import home_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.home.schemas import HomeMetric
from app.crud.home.services import HomeServices
from app.crud.users import UserInDB

router = APIRouter(tags=["Home"])


@router.get("/home", responses={200: {"model": HomeMetric}})
async def get_home_metrics(
    current_user: UserInDB = Security(decode_jwt, scopes=[]),
    metric_services: HomeServices = Depends(home_composer),
):
    home_metric = await metric_services.get_home_metrics()

    if home_metric:
        return build_response(
            status_code=200, message="Home metrics found with success", data=home_metric
        )

    else:
        return Response(status_code=204)
