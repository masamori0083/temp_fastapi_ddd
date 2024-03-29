"""
ユーザーモデルの定義
ユーザーのデータベースモデル、ユーザーの作成、更新、パスワードの更新、公開用モデルを分けて定義
パスワードとソルトをUserBaseとUserPublicに含めないようにし、バックエンドに情報が残らないようにする。
"""

import string
from typing import Optional

from app.models.core import CoreModel, DateTimeModelMixin, IDModelMixin
from app.models.profile import ProfilePublic
from app.models.token import AccessToken
from pydantic import EmailStr, constr


def validate_username(username: str) -> str:
    allowed = string.ascii_letters + string.digits + "-" + "_"
    assert all(
        char in allowed for char in username
    ), "ユーザー名に無効な文字が含まれています。"
    assert len(username) >= 3, "ユーザー名は3文字以上である必要があります。"
    return username


class UserBase(CoreModel):
    email: Optional[EmailStr]
    username: Optional[str]
    email_verified: bool = False
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(CoreModel):
    email: EmailStr
    password: constr(min_length=7, max_length=100)
    username: constr(min_length=3, pattern="[a-zA-Z0-9_-]+$")


class UserUpdate(CoreModel):
    email: Optional[EmailStr]
    username: Optional[constr(min_length=3, pattern="[a-zA-Z0-9_-]+$")]


class UserPasswordUpdate(CoreModel):
    password: constr(min_length=7, max_length=100)
    salt: str


class UserInDB(IDModelMixin, DateTimeModelMixin, UserBase):
    """
    DB内のユーザー情報を表すモデル
    """

    password: constr(min_length=7, max_length=100)
    salt: str


class UserPublic(IDModelMixin, DateTimeModelMixin, UserBase):
    """
    他のユーザーに公開されるユーザー情報を表すモデル
    """

    access_token: Optional[AccessToken]
    profile: Optional[ProfilePublic]
