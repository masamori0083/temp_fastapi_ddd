from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.db.repositories.users import UsersRepository
from app.models.token import AccessToken
from app.models.user import UserCreate, UserInDB, UserPublic, UserUpdate
from app.services import auth_service
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from starlette.status import HTTP_201_CREATED

router = APIRouter()


@router.post(
    "/",
    response_model=UserPublic,
    name="users:register-new-user",
    status_code=HTTP_201_CREATED,
)
async def register_new_user(
    new_user: UserCreate = Body(..., embed=True),
    user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> UserPublic:
    created_user = await user_repo.register_new_user(new_user=new_user)
    access_token = AccessToken(
        access_token=auth_service.create_access_token_for_user(user=created_user),
        token_type="bearer",
    )
    return created_user.model_copy(update={"access_token": access_token})


@router.post(
    "/login/token", response_model=AccessToken, name="users:login-email-and-password"
)
async def user_login_with_email_and_password(
    user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm),
) -> AccessToken:
    """
    トークン作成のエンドポイント
    """
    user = await user_repo.authenticate_user(
        email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication was unsuccessful",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = AccessToken(
        access_token=auth_service.create_access_token_for_user(user=user),
        token_type="bearer",
    )
    return access_token


@router.get("/me/", response_model=UserPublic, name="users:get-current-user")
async def get_currenctly_authenticated_user(
    current_user: UserInDB = Depends(get_current_active_user),
) -> UserPublic:
    return current_user
