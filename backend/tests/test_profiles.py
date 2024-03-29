import pytest
from app.db.repositories.profiles import ProfilesRepository
from app.models.profile import ProfileInDB, ProfilePublic
from app.models.user import UserInDB, UserPublic
from databases import Database
from fastapi import FastAPI, status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestProfilesRoutes:
    """
    2つのプロフィール関連のエンドポイントが存在することを確認するテスト
    """

    async def test_routes_exist(
        self, app: FastAPI, client: AsyncClient, test_user: UserInDB
    ) -> None:
        res = await client.get(
            app.url_path_for(
                "profiles:get-profile-by-username", username=test_user.username
            )
        )
        assert res.status_code != status.HTTP_404_NOT_FOUND

        res = await client.put(
            app.url_path_for("profiles:update-own-profile"), json={"profile_update": {}}
        )
        assert res.status_code != status.HTTP_404_NOT_FOUND


class TestProfileCreate:
    async def test_profile_created_for_new_users(
        self, app: FastAPI, client: AsyncClient, db: Database
    ) -> None:
        profiles_repo = ProfilesRepository(db)
        new_user = {
            "email": "nmomos@mail.com",
            "username": "nmomoishedgehog",
            "password": "nmomosissocute",
        }
        res = await client.post(
            app.url_path_for("users:register-new-user"), json={"new_user": new_user}
        )
        assert res.status_code == status.HTTP_201_CREATED
        created_user = UserPublic(**res.json())
        user_profile = await profiles_repo.get_profile_by_user_id(
            user_id=created_user.id
        )
        assert user_profile is not None
        assert isinstance(user_profile, ProfileInDB)


class TestProfileView:
    async def test_authenticated_user_can_view_other_user_profile(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_user: UserInDB,
        test_user2: UserInDB,
    ) -> None:
        """
        認可されたユーザーが他のユーザーのプロフィールを取得できることを確認するテスト
        """
        res = await authorized_client.get(
            app.url_path_for(
                "profiles:get-profile-by-username", username=test_user2.username
            )
        )
        assert res.status_code == status.HTTP_200_OK
        profile = ProfilePublic(**res.json())
        assert profile.username == test_user2.username

    async def test_unregistered_users_cannnot_access_other_user_profile(
        self, app: FastAPI, client: AsyncClient, test_user2: UserInDB
    ) -> None:
        """
        認可されていないユーザーが他のユーザーのプロフィールを取得できないことを確認するテスト
        """
        res = await client.get(
            app.url_path_for(
                "profiles:get-profile-by-username", username=test_user2.username
            )
        )
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_no_profile_is_returned_when_username_matches_no_user(
        self, app: FastAPI, authorized_client: AsyncClient
    ) -> None:
        """
        ユーザー名が一致しない場合、プロフィールが返されないことを確認するテスト
        """
        res = await authorized_client.get(
            app.url_path_for(
                "profiles:get-profile-by-username", username="user_doesnt_match"
            )
        )
        assert res.status_code == status.HTTP_404_NOT_FOUND


class TestProfileManagement:
    @pytest.mark.parametrize(
        "attr, value",
        (
            ("full_name", "Nmomos Hedgehog"),
            ("phone_number", "111-222-3333"),
            ("bio", "This is a test bio"),
            (
                "image",
                "https://nmomos.com/wp-content/uploads/2019/07/cropped-img_0728.jpg",
            ),
        ),
    )
    async def test_user_can_update_own_profile(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_user: UserInDB,
        attr: str,
        value: str,
    ) -> None:
        """
        ユーザープロファイルを更新できることを確認するテスト
        """
        assert getattr(test_user.profile, attr) != value
        res = await authorized_client.put(
            app.url_path_for("profiles:update-own-profile"),
            json={"profile_update": {attr: value}},
        )
        assert res.status_code == status.HTTP_200_OK
        profile = ProfilePublic(**res.json())
        assert getattr(profile, attr) == value

    @pytest.mark.parametrize(
        "attr, value, status_code",
        (
            ("full_name", [], 422),
            ("bio", {}, 422),
            ("image", "./image-string.png", 422),
            ("image", 5, 422),
        ),
    )
    async def test_user_recieves_error_for_invalid_update_params(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_user: UserInDB,
        attr: str,
        value: str,
        status_code: int,
    ) -> None:
        res = await authorized_client.put(
            app.url_path_for("profiles:update-own-profile"),
            json={"profile_update": {attr: value}},
        )
        assert res.status_code == status_code
