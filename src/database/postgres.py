import logging
from omegaconf import DictConfig
from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import scoped_session, sessionmaker

from src.database.repository import PapyrusEmbeddingRepository
from src.health.health import HealthMixin, Health

log = logging.getLogger(__name__)


class Postgres(HealthMixin):
    def __init__(self, database, host, user, password, port):
        url = URL.create(
            'postgresql',
            username=user,
            password=password,
            host=host,
            port=port,
            database=database,
        )
        engine = create_engine(url)
        self.session_f = scoped_session(sessionmaker(autoflush=True, bind=engine))
        self.papyrus_embedding_repository = PapyrusEmbeddingRepository(self.session_f)

    def health(self):
        with self.session_f() as session:
            try:
                session.execute(text('SELECT 1'))
                return Health.OK
            except OperationalError:
                log.error('Postgres interaction not possible')
                return Health.NOT_OK

    @staticmethod
    def from_config(cfg: DictConfig) -> 'Postgres':
        return Postgres(
            database=cfg.database.db,
            host=cfg.database.host,
            user=cfg.database.user,
            password=cfg.database.password,
            port=cfg.database.port,
        )
