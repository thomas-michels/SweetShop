from fastapi import APIRouter, Depends, Security, Response

from app.api.composers import metric_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.metrics.schemas import HomeMetric
from app.crud.metrics.services import MetricServices
from app.crud.users import UserInDB

router = APIRouter(tags=["Metrics"])


@router.get("/home/metrics", responses={200: {"model": HomeMetric}})
async def get_home_metrics(
    current_user: UserInDB = Security(decode_jwt, scopes=[]),
    metric_services: MetricServices = Depends(metric_composer),
):
    home_metric = await metric_services.get_home_metrics()

    if home_metric:
        return build_response(
            status_code=200, message="Billings for dashboard found with success", data=home_metric
        )

    else:
        return Response(status_code=204)
