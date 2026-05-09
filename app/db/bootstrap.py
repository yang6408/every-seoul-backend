import logging

import psycopg
from psycopg import sql

from app.core.config import settings

logger = logging.getLogger(__name__)


def create_database_if_missing() -> None:
    with psycopg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        dbname="postgres",
        autocommit=True,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (settings.DB_NAME,))
            if cur.fetchone():
                logger.info("Database already exists: %s", settings.DB_NAME)
                return

            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(settings.DB_NAME)))
            logger.info("Database created: %s", settings.DB_NAME)
