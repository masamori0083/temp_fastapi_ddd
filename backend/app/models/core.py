"""
モデルで共通するロジック
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from pydantic import BaseModel, validator

JST = timezone(timedelta(hours=+9), "JST")


class CoreModel(BaseModel):
    """
    共通ロジックを持つモデル
    """

    pass


class DateTimeModelMixin(BaseModel):
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @validator("created_at", "updated_at", pre=True)
    def default_datetime(cls, value: datetime) -> datetime:
        return value or datetime.now(JST)


class IDModelMixin(CoreModel):
    """
    IDを持つモデルのためのミックスイン
    """

    id: int
