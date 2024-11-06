import io
import logging
from hydra import compose
from celery import Celery
from celery import chain
from src.storage.minio import MinioClient
from src.database.postgres import Postgres
from PIL import Image
import requests


cfg = compose(config_name='config')

log = logging.getLogger(__name__)

celery = Celery(
    __name__,
    broker=cfg.worker.broker_url,
    backend=cfg.worker.backend_url,
)


def papyrus_retrieval(image_name):
    workflow = chain(compute_embedding_task.s(image_name) | retrieve_similar_papyrus_task.s())
    result = workflow()
    return result


@celery.task
def compute_embedding_task(image_name):
    embedding = compute_embedding(image_name)
    return embedding


@celery.task
def retrieve_similar_papyrus_task(embedding):
    urls = retrieve_similar_papyrus(embedding)
    return urls


def compute_embedding(image_name):
    image = download_image_from_minio(image_name)
    response = send_image_to_litserve(image)
    return response.get('embedding')


def retrieve_similar_papyrus(embedding):
    database = Postgres.from_config(cfg)
    urls = database.papyrus_embedding_repository.get_k_nearest_embeddings(embedding, k=1)
    return urls


def download_image_from_minio(image_name):
    minio_client = MinioClient.from_config(cfg)
    bucket_name = cfg.storage.buckets[0]
    response = minio_client.client.get_object(bucket_name, image_name)
    image_data = response.read()
    image = Image.open(io.BytesIO(image_data))
    return image


def send_image_to_litserve(image):
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    files = {'request': ('image.jpg', img_byte_arr, 'image/jpeg')}
    # response = requests.post("http://127.0.0.1:8001/predict", files=files)
    response = requests.post(cfg.inference.url + '/predict', files=files)
    if response.status_code == 200:
        log.info(f'Prediction result: {response.json}')
    else:
        log.info(f'Error: {response.text}')

    return response.json()
