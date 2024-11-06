import logging
from fastapi import APIRouter
from src.storage.minio import MinioClient
from pydantic import BaseModel, Field
from starlette.requests import Request
from src.database.postgres import Postgres
from src.health.health import Health
from hydra import compose
import httpx


router = APIRouter(prefix='/health', tags=['health'])

log = logging.getLogger(__name__)

cfg = compose(config_name='config')


class HealthResponse(BaseModel):
    storage: Health = Field(description='Storage health status')
    database: Health = Field(description='Database health status')
    inference: Health = Field(description='Inference server health status')


@router.get('', status_code=200, description='Verify whether the application API is operational')
async def health(request: Request) -> HealthResponse:
    inference_health = await __check_litserve()

    return HealthResponse(
        storage=__check_minio(request.app.state.minio_client).value,
        database=__check_postgres(request.app.state.database).value,
        inference=inference_health.value,
    )


def __check_minio(minio: MinioClient):
    return minio.health()


def __check_postgres(postgres: Postgres):
    return postgres.health()


async def __check_litserve():
    """Check the health of the inference server asynchronously."""
    url = cfg.inference.url + '/health'
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                return Health.OK
            else:
                log.error(f'Inference server health check failed with status {response.status_code}')
                return Health.NOT_OK
    except httpx.RequestError as exc:
        log.error(f'Error checking inference server health: {exc}')
        return Health.NOT_OK
