import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    verify_password,
)
from app.crud.user import (
    authenticate_user,
    change_password,
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    update_user,
)
from app.schemas.user import (
    PasswordChange,
    Token,
    TokenRefresh,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.api.dependencies import CurrentUser, get_current_user, SessionDep
from app.models.user import User

router = APIRouter()


def _tokens_for(user: User) -> dict:
    sub = {"sub": str(user.id)}
    return {
        "access_token": create_access_token(data=sub),
        "refresh_token": create_refresh_token(data=sub),
        "token_type": "bearer",
    }


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: SessionDep):
    """Register a new user."""
    # Check if email already exists
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    if get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    user = create_user(db, user_data)
    return user


@router.post("/login", response_model=Token)
async def login(db: SessionDep, form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _tokens_for(user)


@router.post("/refresh", response_model=Token)
async def refresh_token(body: TokenRefresh, db: SessionDep):
    """Exchange a valid refresh token for a fresh access+refresh pair (sliding
    session). Rejects access tokens and anything that doesn't decode."""
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(body.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise invalid
    sub = payload.get("sub")
    if sub is None:
        raise invalid
    try:
        user_id = uuid.UUID(sub)
    except (ValueError, TypeError):
        raise invalid
    user = get_user_by_id(db, user_id=user_id)
    if user is None or not user.is_active:
        raise invalid
    return _tokens_for(user)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user info."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(body: UserUpdate, db: SessionDep, current_user: CurrentUser):
    """Edit the current user's username and/or email. Both optional; each must
    stay unique across users."""
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        return current_user

    if "email" in fields and fields["email"] != current_user.email:
        existing = get_user_by_email(db, fields["email"])
        if existing and existing.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
    if "username" in fields and fields["username"] != current_user.username:
        existing = get_user_by_username(db, fields["username"])
        if existing and existing.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )
    try:
        return update_user(db, current_user, fields)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already in use",
        )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_my_password(
    body: PasswordChange, db: SessionDep, current_user: CurrentUser
):
    """Change the current user's password after verifying the current one."""
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    change_password(db, current_user, body.new_password)
    return None
