from typing import Callable, Type

from app.db.repositories.base import BaseRepository
from databases import Database
from fastapi import Depends
from starlette.requests import Request


def get_database(requet: Request) -> Database:
    return requet.app.state._db


def get_repository(Repo_type: Type[BaseRepository]) -> Callable:
    def get_repo(db: Database = Depends(get_database)) -> Type[BaseRepository]:
        return Repo_type(db)

    return get_repo
