import psycopg
from pgvector.psycopg import register_vector

from .config import settings


def connect() -> psycopg.Connection:
    conn = psycopg.connect(settings.database_url, autocommit=False)
    register_vector(conn)
    return conn
