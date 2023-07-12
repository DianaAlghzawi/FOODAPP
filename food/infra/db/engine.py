from os import getenv

from sqlalchemy import MetaData, create_engine


def get_db_url() -> str:
    return 'postgresql://%s:%s@%s:%s/%s' % (
        getenv('POSTGRES_USER', 'postgres'),
        getenv('POSTGRES_PASSWORD', 'password'),
        getenv('POSTGRES_HOST', 'localhost'),
        getenv('PGPORT', '5432'),
        getenv('PGDATABASE', 'food'),
    )


engine = create_engine(get_db_url())
metadata = MetaData()
