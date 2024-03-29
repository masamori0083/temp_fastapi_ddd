"""
トークンを作成するためのモデル
"""

from datetime import datetime, timedelta, timezone

from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_AUDIENCE
from app.models.core import CoreModel
from pydantic import EmailStr


class JWTMeta(CoreModel):
    """
    JWTのメタデータ(追加情報)を表すモデル
    """

    iss: str = "hedgehog-reservation.com"  # JWTの発行者の名前
    aud: str = JWT_AUDIENCE  # JWTの受信者の名前
    iat: float = datetime.timestamp(datetime.now(timezone.utc))  # JWTの発行日時
    exp: float = datetime.timestamp(
        datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )  # JWTの有効期限


class JWTCreds(CoreModel):
    sub: EmailStr  # JWTのサブジェクト(ユーザーのメールアドレス)
    username: str  # JWTのユーザー名


class JWTPayload(JWTMeta, JWTCreds):
    """
    JWTのペイロード(本文)を表すモデル
    """

    pass


class AccessToken(CoreModel):
    """
    アクセストークンを表すモデル
    """

    access_token: str
    token_type: str
