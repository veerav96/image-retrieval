from minio import Minio
from minio.error import MinioException, S3Error
from omegaconf import DictConfig
from src.health.health import HealthMixin, Health
import logging

log = logging.getLogger(__name__)


class MinioClient(HealthMixin):
    def __init__(self, endpoint, access_key, secret_key, secure=True):
        self.client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)

    def ensure_bucket(self, bucket_name: str):
        """Ensure a single bucket exists, and create it if not present."""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                log.info(f'Bucket {bucket_name} created.')
            else:
                log.info(f'Bucket {bucket_name} already exists.')
        except S3Error as e:
            log.error(f'Error ensuring bucket {bucket_name}: {e}')

    def ensure_buckets(self, bucket_list: list):
        """Ensure all buckets exist based on the list provided."""
        for bucket_name in bucket_list:
            self.ensure_bucket(bucket_name)

    def health(self) -> Health:
        """perform a health check."""
        try:
            self.client.list_buckets()
            return Health.OK
        except MinioException:
            log.error('Minio interaction not possible')
            return Health.NOT_OK

    @staticmethod
    def from_config(cfg: DictConfig) -> 'MinioClient':
        """Initialize configuration"""
        minio_client = MinioClient(
            endpoint=cfg.storage.endpoint,
            access_key=cfg.storage.access_key,
            secret_key=cfg.storage.secret_key,
            secure=cfg.storage.secure,
        )
        minio_client.ensure_buckets(cfg.storage.buckets)
        return minio_client
