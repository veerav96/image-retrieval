import logging
import uuid
from typing import TypeVar, Generic, Optional, Type, List, Any, get_origin, get_args
from uuid import UUID

from sqlalchemy import Column, UUID as AlchemyUUID, DateTime, func, String
from sqlalchemy.exc import ProgrammingError, OperationalError
from sqlalchemy.orm import declarative_base, scoped_session
from pgvector.sqlalchemy import Vector
from sqlalchemy import text


log = logging.getLogger(__name__)

Base = declarative_base()


class PapyrusEmbeddingEntity(Base):
    __tablename__ = 'papyrus_embedding'

    id = Column(
        AlchemyUUID,
        primary_key=True,
        index=True,
        nullable=False,
        default=lambda: uuid.uuid4(),
    )
    url = Column(String, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    modified_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    embedding = Column(Vector(128), nullable=False)


T_co = TypeVar('T_co', bound=Base)


class Repository(Generic[T_co]):
    _model: Optional[Type[T_co]] = None

    @classmethod
    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__orig_bases__:  # type: ignore[attr-defined]
            origin = get_origin(base)
            if origin is None or not issubclass(origin, Repository):
                continue
            type_arg = get_args(base)[0]
            if not isinstance(type_arg, TypeVar):
                cls._model = type_arg
                return
        assert cls._model, 'Could not initialise the repository'

    def __init__(self, session_f: scoped_session):
        self.session_f = session_f
        self.verify_schema()

    def verify_schema(self):
        try:
            log.debug(f'Running "{self._model.__tablename__}" repository schema verification')
            with self.session_f() as session:
                session.query(self._model).first()
        except (ProgrammingError, OperationalError) as e:
            raise RepositorySchemaVerificationException(
                f'schema verification failed for the "{self._model.__tablename__}" repository '
            ) from e
        log.info(f'"{self._model.__tablename__}" repository schema verification completed')

    def get(self, id: UUID) -> Optional[T_co]:
        with self.session_f() as session:
            return session.query(self._model).filter(self._model.id == id).first()

    def list(self, skip: int = 0, limit: int = 100) -> List[T_co]:
        with self.session_f() as session:
            return session.query(self._model).offset(skip).limit(limit).all()

    def save(self, obj: T_co) -> T_co:
        with self.session_f() as session:
            obj = session.merge(obj)
            session.commit()
            session.refresh(obj)
            return obj

    def delete(self, id: UUID):
        with self.session_f() as session:
            session.query(self._model).filter(self._model.id == id).delete()
            session.commit()


class RepositorySchemaVerificationException(Exception):
    pass


class PapyrusEmbeddingRepository(Repository[PapyrusEmbeddingEntity]):
    def get_by_url(self, url: str) -> Optional[PapyrusEmbeddingEntity]:
        """
        Retrieve a PapyrusEmbeddingEntity by its url.

        :param url: The url to search for.
        :return: PapyrusEmbeddingEntity object or None if not found.
        """
        with self.session_f() as session:
            return session.query(self._model).filter(self._model.url == url).first()

    def get_k_nearest_embeddings(self, embedding: List[float], k: int) -> List[PapyrusEmbeddingEntity]:
        """
        Retrieve the top k nearest embeddings based on cosine similarity.

        :param embedding: The query embedding as a list of floats.
        :param k: Number of nearest neighbors to retrieve.
        :return: List of PapyrusEmbeddingEntity objects corresponding to the top k nearest embeddings.
        """
        with self.session_f() as session:
            query = text(f"""
            SELECT url,
                1 - (embedding <=> CAST(:embedding AS vector)) AS cosine_similarity
            FROM {self._model.__tablename__}
            ORDER BY 1 - (embedding <=> CAST(:embedding AS vector)) DESC  -- Order by cosine similarity, descending
            LIMIT :k
            """)
            log.info(f'Query: {query}')
            log.info(f'Params: embedding={embedding}, k={k}')
            log.info(f'Type of embedding: {type(embedding)}')
            log.info(f'Type of k: {type(k)}')

            result = session.execute(query, {'embedding': embedding, 'k': k}).fetchall()

            # Log the cosine similarity values
            for row in result:
                log.info(f'URL: {row[0]}, Cosine Similarity: {row[1]}')

            urls = [row[0] for row in result]
            return urls

    def update_embedding(self, id: UUID, new_embedding: List[float]) -> Optional[PapyrusEmbeddingEntity]:
        """
        Update the embedding vector of a given PapyrusEmbeddingEntity.

        :param id: The UUID of the PapyrusEmbeddingEntity to update.
        :param new_embedding: The new embedding vector as a list of floats.
        :return: The updated PapyrusEmbeddingEntity object or None if not found.
        """
        with self.session_f() as session:
            obj = session.query(self._model).filter(self._model.id == id).first()
            if obj:
                obj.embedding = new_embedding
                session.commit()
                session.refresh(obj)
                return obj
            return None

    def delete_by_url(self, url: str) -> None:
        """
        Delete a PapyrusEmbeddingEntity by its url.

        :param url: The url of the PapyrusEmbeddingEntity to delete.
        """
        with self.session_f() as session:
            session.query(self._model).filter(self._model.url == url).delete()
            session.commit()

    def bulk_insert(self, entities: List[PapyrusEmbeddingEntity]) -> None:
        """
        Bulk insert multiple PapyrusEmbeddingEntities.

        :param embeddings: A list of PapyrusEmbeddingEntity objects to insert.
        """
        with self.session_f() as session:
            session.bulk_save_objects(entities)
            session.commit()
