from contextlib import asynccontextmanager
from pathlib import Path
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
import uvicorn
import yaml
import os
import logging
from hydra import compose
from src.database.postgres import Postgres
from src.storage.minio import MinioClient
from src.api import papyrus_retrieval, health

config_dir = os.getenv('PAPYRUS_APP_CONFIG_DIR', str(Path(__file__).resolve().parent.parent / 'config'))
log_level = os.getenv('LOG_LEVEL', 'INFO')
log_config = f'{config_dir}/logging/logging.yaml'
log = logging.getLogger(__name__)


@asynccontextmanager
async def configure_dependencies(app: FastAPI):
    log.info('Initialising...')

    cfg = compose(config_name='config')

    app.state.minio_client = MinioClient.from_config(cfg)
    app.state.database = Postgres.from_config(cfg)

    log.info('Initialisation completed')
    yield


description = """
Image search to fetch information about a given papyrus.
"""

api = FastAPI(title='Papyrus Retrieval', description=description, lifespan=configure_dependencies)

api.include_router(health.router)
api.include_router(papyrus_retrieval.router)
api.mount('/static', StaticFiles(directory=Path(__file__).resolve().parent / 'ui' / 'static'), name='static')
templates = Jinja2Templates(directory=Path(__file__).resolve().parent / 'ui' / 'templates')


description = """
Image search to fetch information about a given papyrus.
"""


@api.get('/', response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@api.get('/docs', include_in_schema=False)
def overridden_swagger():
    return get_swagger_ui_html(
        openapi_url='/openapi.json',
        title='Papyus Image Retrieval',
        swagger_favicon_url='/favicon.ico',
    )


if __name__ == '__main__':
    logging.basicConfig(level=log_level.upper())

    with open(log_config) as file:
        logging.config.dictConfig(yaml.safe_load(file))

    log.info('Starting Papyrus Retrieval Utility')
    uvicorn.run(
        'main:api',
        host='0.0.0.0',
        port=int(os.getenv('PAPYRUS_API_PORT', 8000)),
        log_config=log_config,
        log_level=log_level.lower(),
        workers=int(os.getenv('PAPYRUS_API_WORKERS', 1)),
    )
