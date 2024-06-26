import logging
import os

from app.core.config import DATABASE_URL
from databases import Database
from fastapi import FastAPI

logger = logging.getLogger(__name__)


async def connect_to_db(app: FastAPI) -> None:
    """
    DBに接続する関数。
    """
    CONTAINER_DSN = os.getenv("CONTAINER_DSN", "")
    DB_URL = (
        CONTAINER_DSN if CONTAINER_DSN else DATABASE_URL
    )  # テスト環境とで接続先を変える
    database = Database(DATABASE_URL, min_size=2, max_size=5)

    try:
        await database.connect()
        app.state._db = database
    except Exception as e:
        logger.warn("--- DATABASE CONNECTION ERROR ---")
        logger.warn(e)
        logger.warn("--- DATABASE CONNECTION ERROR ---")


async def close_db_connection(app: FastAPI) -> None:
    try:
        await app.state._db.disconnect()
    except Exception as e:
        logger.warn("--- DATABASE DISCONNECTION ERROR ---")
        logger.warn(e)
        logger.warn("--- DATABASE DISCONNECTION ERROR ---")
