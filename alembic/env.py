from logging.config import fileConfig
 
from sqlalchemy import engine_from_config
from sqlalchemy import create_engine, pool
 
from alembic import context
from app.models import Base
 
# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
 
# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
 
# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata
 
# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
 
 
def run_migrations_online():
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool
    )
 
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
 
        with context.begin_transaction():
            context.run_migrations()
 
if context.is_offline_mode():
    # Running migrations offline
    context.configure(url=config.get_main_option("sqlalchemy.url"))
    with context.begin_transaction():
        context.run_migrations()
else:
    # Running migrations online
    run_migrations_online()
 
 