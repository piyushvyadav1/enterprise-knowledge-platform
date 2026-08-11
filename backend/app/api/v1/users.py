from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session
from app.schemas.user import (
    AdminUserCreate,
    UserResponse,
    UserRoleUpdate,
    AdminResetPasswordRequest,
)

from app.auth.dependencies import require_roles
from app.auth.security import hash_password
from app.database.database import get_db
from app.models.user import User
from app.schemas.user import (
    AdminUserCreate,
    UserResponse,
    UserRoleUpdate,
    UserDepartmentUpdate,
    UserStatusUpdate,
)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

ALLOWED_ROLES = {
    "admin",
    "knowledge_manager",
    "ceo",
    "hr",
    "tl",
    "employee",
}

ALLOWED_DEPARTMENTS = {
    "general",
    "hr",
    "sales",
    "marketing",
    "finance",
    "it",
    "operations",
}


@router.get(
    "/",
    response_model=list[UserResponse],
)
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(["admin"])
    ),
):
    return (
        db.query(User)
        .order_by(User.id.asc())
        .all()
    )


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user_data: AdminUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(["admin"])
    ),
):
    email = user_data.email.lower().strip()
    role = user_data.role.strip().lower()
    department = user_data.department.strip()

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    if role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user role",
        )

    department_map = {
        value.lower(): value
        for value in [
            "General",
            "HR",
            "Sales",
            "Marketing",
            "Finance",
            "IT",
            "Operations",
        ]
    }

    if department.lower() not in department_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid department",
        )

    new_user = User(
        name=user_data.name.strip(),
        email=email,
        password_hash=hash_password(
            user_data.password
        ),
        role=role,
        department=department_map[
            department.lower()
        ],
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
)
def update_user_role(
    user_id: int,
    role_data: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(["admin"])
    ),
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    new_role = role_data.role.strip().lower()

    if new_role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user role",
        )

    if user.id == current_user.id and new_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot downgrade your own administrator account",
        )

    user.role = new_role
    db.commit()
    db.refresh(user)

    return user


@router.patch(
    "/{user_id}/department",
    response_model=UserResponse,
)
def update_user_department(
    user_id: int,
    department_data: UserDepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(["admin"])
    ),
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    department_map = {
        value.lower(): value
        for value in [
            "General",
            "HR",
            "Sales",
            "Marketing",
            "Finance",
            "IT",
            "Operations",
        ]
    }

    normalized = department_data.department.strip().lower()

    if normalized not in department_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid department",
        )

    user.department = department_map[normalized]

    db.commit()
    db.refresh(user)

    return user


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
)
def update_user_status(
    user_id: int,
    status_data: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(["admin"])
    ),
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.id == current_user.id and not status_data.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot pause your own administrator account",
        )

    user.is_active = status_data.is_active

    db.commit()
    db.refresh(user)

    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(["admin"])
    ),
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own administrator account",
        )

    db.delete(user)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This user cannot be deleted because other records "
                "are linked to the account. Pause the user instead."
            ),
        )

    return None

# =========================================================
# ADMIN RESET USER PASSWORD
# =========================================================

@router.patch(
    "/{user_id}/password",
)
def reset_user_password(
    user_id: int,
    password_data: AdminResetPasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(["admin"])
    ),
):

    # -----------------------------------------------------
    # Find target user
    # -----------------------------------------------------

    user = (
        db.query(User)
        .filter(
            User.id == user_id
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # -----------------------------------------------------
    # Hash new password
    # -----------------------------------------------------

    user.password_hash = hash_password(
        password_data.new_password
    )

    db.commit()

    return {
        "message": (
            f"Password reset successfully "
            f"for {user.name}."
        )
    }