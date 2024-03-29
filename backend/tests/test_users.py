from typing import List, Optional, Type, Union

import jwt
import pytest
from app.core.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_AUDIENCE,
    JWT_TOKEN_PREFIX,
    SECRET_KEY,
)
from app.db.repositories.users import UsersRepository
from app.models.token import JWTCreds, JWTMeta, JWTPayload
from app.models.user import UserCreate, UserInDB, UserPublic
from app.services import auth_service
from databases import Database
from fastapi import FastAPI, HTTPException
from httpx import AsyncClient
from pydantic import ValidationError
from starlette.datastructures import Secret
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

pytestmark = pytest.mark.asyncio


class TestUsersRoutes:
    """
    ユーザー登録のルートが存在することを確認するテスト。
    """

    async def test_routes_exists(self, app: FastAPI, client: AsyncClient) -> None:
        new_user = {
            "email": "test@email.com",
            "username": "test_username",
            "password": "testpassword",
        }

        res = await client.post(
            app.url_path_for("users:register-new-user"), json={"new_user": new_user}
        )
        assert res.status_code != HTTP_404_NOT_FOUND


class TestUserRegistration:
    """
    ユーザー登録のAPIテスト。
    """

    async def test_users_can_register_successfully(
        self, app: FastAPI, client: AsyncClient, db: Database
    ) -> None:
        user_repo = UsersRepository(db)
        new_user = {
            "email": "foo@bar.com",
            "username": "foobar",
            "password": "bazquxquux",
        }

        user_in_db = await user_repo.get_user_by_email(email=new_user["email"])
        assert user_in_db is None

        res = await client.post(
            app.url_path_for("users:register-new-user"), json={"new_user": new_user}
        )
        assert res.status_code == HTTP_201_CREATED

        user_in_db = await user_repo.get_user_by_email(email=new_user["email"])
        assert user_in_db is not None
        assert user_in_db.email == new_user["email"]
        assert user_in_db.username == new_user["username"]

        created_user = UserInDB(
            **res.json(), password="whatever", salt="123"
        ).model_dump(exclude={"password", "salt"})

        assert created_user == UserInDB(**user_in_db.model_dump()).model_dump(
            exclude={"password", "salt"}
        )

    @pytest.mark.parametrize(
        "attr, value, status_code",
        (
            ("email", "foo@bar.com", 400),
            ("username", "foobar", 400),
            ("email", "invalid_email@one@two.com", 422),
            ("password", "short", 422),
            ("username", "foobar@#$%^<>", 422),
            ("username", "ab", 422),
        ),
    )
    async def test_user_registration_fails_when_credentials_are_taken(
        self,
        app: FastAPI,
        client: AsyncClient,
        attr: str,
        value: str,
        status_code: int,
    ) -> None:
        new_user = {
            "email": "nottaken@email.com",
            "username": "not_taken_username",
            "password": "foobarpassword",
        }
        new_user[attr] = value

        res = await client.post(
            app.url_path_for("users:register-new-user"), json={"new_user": new_user}
        )
        assert res.status_code == status_code

    async def test_users_saved_password_is_hashed_and_has_salt(
        self, app: FastAPI, client: AsyncClient, db: Database
    ) -> None:
        user_repo = UsersRepository(db)
        new_user = {
            "email": "nmomo@mail.com",
            "username": "nmomo",
            "password": "nmomoishedgehog",
        }

        res = await client.post(
            app.url_path_for("users:register-new-user"), json={"new_user": new_user}
        )
        assert res.status_code == HTTP_201_CREATED

        user_in_db = await user_repo.get_user_by_email(email=new_user["email"])
        await user_in_db is not None
        await user_in_db.salt is not None and user_in_db.salt != "123"
        assert user_in_db.password != new_user["password"]
        assert auth_service.veryfy_password(
            password=new_user["password"],
            salt=user_in_db.salt,
            hashed_pw=user_in_db.password,
        )


class TestAuthTokens:
    async def test_can_create_access_token_successfully(
        self, app: FastAPI, client: AsyncClient, test_user: UserInDB
    ) -> None:
        """
        AuthServiceクラスを使ってユーザのアクセストークンを作成できるかどうかをテスト
        """
        access_token = auth_service.create_access_token_for_user(
            user=test_user,
            secret_key=str(SECRET_KEY),
            audience=JWT_AUDIENCE,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        creds = jwt.decode(
            access_token,
            str(SECRET_KEY),
            audience=JWT_AUDIENCE,
            algorithms=[JWT_ALGORITHM],
        )
        assert creds.get("username") is not None
        assert creds["username"] == test_user.username
        assert creds["aud"] == JWT_AUDIENCE

    async def test_token_missing_user_is_invalid(
        self, app: FastAPI, client: AsyncClient
    ) -> None:
        """
        トークンにユーザがエンコードされていない場合のテストを行い、
        ペイロードに何も含まれていないことを確認。
        """
        access_token = auth_service.create_access_token_for_user(
            user=None,
            secret_key=str(SECRET_KEY),
            audience=JWT_AUDIENCE,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        with pytest.raises(jwt.PyJWTError):
            jwt.decode(
                access_token,
                str(SECRET_KEY),
                audience=JWT_AUDIENCE,
                algorithms=[JWT_ALGORITHM],
            )

    @pytest.mark.parametrize(
        "secret_key, jwt_audience, exception",
        (
            ("wrong-secret", JWT_AUDIENCE, jwt.InvalidSignatureError),
            (None, JWT_AUDIENCE, jwt.InvalidTokenError),
            (SECRET_KEY, "othersite:auth", jwt.InvalidAudienceError),
            (SECRET_KEY, None, ValidationError),
        ),
    )
    async def test_invalid_token_content_raises_error(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_user: UserInDB,
        secret_key: Union[str, Secret],
        jwt_audience: str,
        exception: Type[Exception],
    ) -> None:
        """
        特定の条件下で不正なJWT（JSON Web Token）トークンが
        与えられた場合に適切な例外が発生するかを確認することを目的としている
        無効なシークレットとオーディエンスを create_access_token_for_user メソッドに渡し、
        pyjwtパッケージが PyJWTError を発生させることを確認する。
        """
        with pytest.raises(exception):
            access_token = auth_service.create_access_token_for_user(
                user=test_user,
                secret_key=str(secret_key),
                audience=jwt_audience,
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES,
            )
            jwt.decode(
                access_token,
                str(SECRET_KEY),
                audience=JWT_AUDIENCE,
                algorithms=[JWT_ALGORITHM],
            )

    async def test_can_retrieve_username_from_token(
        self, app: FastAPI, client: AsyncClient, test_user: UserInDB
    ) -> None:
        """
        トークンからユーザ名を取得できるかどうかをテスト
        """
        token = auth_service.create_access_token_for_user(
            user=test_user, secret_key=str(SECRET_KEY)
        )
        username = auth_service.get_username_from_token(
            token=token, secret_key=str(SECRET_KEY)
        )
        assert username == test_user.username

    @pytest.mark.parametrize(
        "secret, wrong_token",
        (
            (SECRET_KEY, "asdf"),
            (SECRET_KEY, ""),
            (SECRET_KEY, None),
            ("ABC123", "use correct token"),
        ),
    )
    async def test_error_with_token_or_secret_is_wrong(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_user: UserInDB,
        secret: Union[Secret, str],
        wrong_token: Optional[str],
    ) -> None:
        """
        トークンまたはシークレットが正しくない場合にエラーが発生することを確認するテスト
        """
        token = auth_service.create_access_token_for_user(
            user=test_user, secret_key=str(SECRET_KEY)
        )

        if wrong_token == "user correct token":
            wrong_token = token

        with pytest.raises(HTTPException):
            username = auth_service.get_username_from_token(
                token=wrong_token, secret_key=str(secret)
            )


class TestUserRegistration:
    async def test_users_can_register_successfully(
        self, app: FastAPI, client: AsyncClient, db: Database
    ) -> None:
        user_repo = UsersRepository(db)
        new_user = {
            "email": "foo@bar.com",
            "username": "foobar",
            "password": "bazquxquux",
        }

        user_in_db = await user_repo.get_user_by_email(email=new_user["email"])
        assert user_in_db is None

        res = await client.post(
            app.url_path_for("users:register-new-user"), json={"new_user": new_user}
        )
        assert res.status_code == HTTP_201_CREATED

        user_in_db = await user_repo.get_user_by_email(
            email=new_user["email"], populate=False
        )
        assert user_in_db is not None
        assert user_in_db.email == new_user["email"]
        assert user_in_db.username == new_user["username"]

        created_user = UserPublic(**res.json()).model_dump(exclude={"access_token"})
        assert created_user == user_in_db.model_dump(exclude={"password", "salt"})


class TestUserLogin:
    async def test_user_can_login_successfully_and_receives_valid_token(
        self, app: FastAPI, client: AsyncClient, test_user: UserInDB
    ) -> None:
        """
        レスポンスが有効であり、アクセストークンが正しい形式で返される。
        また、トークンが正しいユーザ情報を含んでいることを確認する。
        """
        client.headers["content-type"] = "application/x-www-form-urlencoded"
        login_data = {
            "username": test_user.email,
            "password": "nmomosissocute",
        }
        res = await client.post(
            app.url_path_for("users:login-email-and-password"), data=login_data
        )
        assert res.status_code == HTTP_200_OK
        token = res.json().get("access_token")
        creds = jwt.decode(
            token, str(SECRET_KEY), audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM]
        )
        assert "username" in creds
        assert creds["username"] == test_user.username
        assert "sub" in creds
        assert creds["sub"] == test_user.email

        assert "token_type" in res.json()
        assert res.json().get("token_type") == "bearer"

    @pytest.mark.parametrize(
        "credential, wrong_value, status_code",
        (
            ("email", "wrong@email.com", 401),
            ("email", None, 401),
            ("email", "notemail", 401),
            ("password", "wrongpassword", 401),
            ("password", None, 401),
        ),
    )
    async def test_user_with_wrong_creds_doesnt_receive_token(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_user: UserInDB,
        credential: str,
        wrong_value: str,
        satus_code: int,
    ) -> None:
        client.headers["content-type"] = "application/x-www-form-urlencoded"
        user_data = test_user.model_dump()
        user_data["password"] = "nmomosissocute"
        user_data[credential] = wrong_value
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"],
        }
        res = await client.post(
            app.url_path_for("users:login-email-and-password"), data=login_data
        )
        assert res.status_code == satus_code
        assert "access_token" not in res.json()


class TetUserMe:
    async def test_authenticated_user_can_retrive_own_data(
        self, app: FastAPI, authorized_client: AsyncClient, test_user: UserInDB
    ) -> None:
        res = await authorized_client.get(app.url_path_for("users:get-current-user"))
        assert res.status_code == HTTP_200_OK
        user = UserPublic(**res.json())
        assert user.email == test_user.email
        assert user.username == test_user.username
        assert user.id == test_user.id

    async def test_user_cannot_access_own_data_if_not_authenticated(
        self, app: FastAPI, client: AsyncClient, test_user: UserInDB
    ) -> None:
        res = await client.get(app.url_path_for("users:get-current-user"))
        assert res.status_code == HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        "jwt_prefix", (("",), ("value",), ("Token",), ("JWT",), ("Swearer",))
    )
    async def test_user_connot_access_own_data_with_incorrect_jwt_prefix(
        self, app: FastAPI, client: AsyncClient, test_user: UserInDB, jwt_prefix: str
    ) -> None:
        """
        jwt_prefixが正しくない場合にアクセスできないことを確認するテスト
        """
        token = auth_service.create_access_token_for_user(
            user=test_user, secret_key=str(SECRET_KEY)
        )
        res = await client.get(
            app.url_path_for("users:get-current-user"),
            headers={"Authorization": f"{jwt_prefix} {token}"},
        )
        assert res.status_code == HTTP_401_UNAUTHORIZED
