"""
マイグレーションを実行するためのスクリプト
Alembic は、SQLAlchemy によって生成されたデーエータベースのスキーマを管理するためのツール
その自動生成されたコードの一部
"""

import logging
import os
import pathlib
import sys
from logging.config import fileConfig

import alembic
from sqlalchemy import engine_from_config, pool

sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))
from app.core.config import DATABASE_URL  # isort:skip

config = alembic.context.config
fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")


def run_migrations_online() -> None:
    CONTAINER_DSN = os.getenv("CONTAINER_DSN", "")
    DB_URL = (
        CONTAINER_DSN if CONTAINER_DSN else DATABASE_URL
    )  # テスト環境とで接続先を変える
    logger.info("Run migrate on {0}".format(str(DB_URL)))

    connectable = config.attributes.get("connection", None)
    config.set_main_option("sqlalchemy.url", str(DB_URL))

    if connectable is None:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
    # 実際のデータベース接続を確立し、Alembicの実行コンテキストを設定するためのもの
    with connectable.connect() as connection:
        alembic.context.configure(connection=connection, target_metadata=None)
        with alembic.context.begin_transaction():
            alembic.context.run_migrations()


run_migrations_online()
