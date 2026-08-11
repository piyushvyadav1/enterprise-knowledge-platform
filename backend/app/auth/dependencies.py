from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.jwt import decode_access_token
from app.database.database import get_db
from app.models.user import User


# ============================================================
# OAUTH2
# ============================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)


# ============================================================
# GET CURRENT USER
# ============================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    Validate the JWT and return the authenticated user.

    IMPORTANT:
    Paused users are denied access even if they still
    possess a previously issued JWT.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    # --------------------------------------------------------
    # Decode token
    # --------------------------------------------------------

    payload = decode_access_token(token)

    if not payload:
        raise credentials_exception

    # --------------------------------------------------------
    # Get user ID
    # --------------------------------------------------------

    user_id = payload.get("sub")

    if not user_id:
        raise credentials_exception

    try:
        user_id = int(user_id)

    except (ValueError, TypeError):
        raise credentials_exception

    # --------------------------------------------------------
    # Find user
    # --------------------------------------------------------

    user = (
        db.query(User)
        .filter(
            User.id == user_id
        )
        .first()
    )

    if not user:
        raise credentials_exception

    # --------------------------------------------------------
    # CHECK ACTIVE STATUS
    # --------------------------------------------------------

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Your account has been paused. "
                "Please contact the administrator."
            ),
        )

    return user


# ============================================================
# ROLE PROTECTION
# ============================================================

def require_roles(
    allowed_roles: List[str],
):
    """
    Restrict an endpoint to specific roles.
    """

    def role_checker(
        current_user: User = Depends(
            get_current_user
        )
    ):
        if current_user.role not in allowed_roles:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You do not have permission "
                    "to perform this action"
                ),
            )

        return current_user

    return role_checker