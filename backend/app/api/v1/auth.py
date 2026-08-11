from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.jwt import create_access_token
from app.auth.security import hash_password, verify_password
from app.database.database import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user

from app.schemas.user import (
    UserRegister,
    UserResponse,
    TokenResponse,
    ChangePasswordRequest,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


ALLOWED_ROLES = {
    "admin",
    "knowledge_manager",
    "employee",
    "guest"
}


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):

    email = user_data.email.lower()

    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    new_user = User(
        name=user_data.name.strip(),
        email=email,
        password_hash=hash_password(
            user_data.password
        ),

        # Public users cannot choose their role.
        role="employee"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    # OAuth2 calls this field "username".
    # For our application, the username is the user's email.
    email = form_data.username.lower()

    user = db.query(User).filter(
        User.email == email
    ).first()

    if not user or not verify_password(
        form_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been paused. Contact an administrator.",
        )

    token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }
from app.auth.dependencies import get_current_user


@router.get(
    "/me",
    response_model=UserResponse
)
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user

# =========================================================
# CHANGE MY PASSWORD
# =========================================================

@router.patch(
    "/change-password"
)
def change_my_password(
    password_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    # -----------------------------------------------------
    # Verify current password
    # -----------------------------------------------------

    if not verify_password(
        password_data.current_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    # -----------------------------------------------------
    # Hash new password
    # -----------------------------------------------------

    current_user.password_hash = hash_password(
        password_data.new_password
    )

    db.commit()

    return {
        "message": "Password changed successfully."
    }