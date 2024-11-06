from logging.config import fileConfig

from sqlalchemy import engine_from_config, URL, pool
from hydra import compose
from alembic import context
from src.database.repository import Base

hydra_cfg = compose(config_name='config')
ini_config = context.config

if ini_config.config_file_name is not None:
    fileConfig(ini_config.config_file_name)

target_metadata = Base.metadata

url = URL.create(
    'postgresql',
    username=hydra_cfg.database.user,
    password=hydra_cfg.database.password,
    host=hydra_cfg.database.host,
    port=hydra_cfg.database.port,
    database=hydra_cfg.database.db,
    query=dict(options='-csearch_path=public'),
)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """

    context.configure(
        url=str(url),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = ini_config.get_section(ini_config.config_ini_section)
    configuration['sqlalchemy.url'] = url
    connectable = engine_from_config(
        configuration,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
