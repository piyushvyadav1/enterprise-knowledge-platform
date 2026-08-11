from pydantic import BaseModel, EmailStr, Field


# =========================================================
# PUBLIC USER REGISTRATION
# =========================================================
#
# Used by:
# POST /auth/register
#
# Public registration always creates:
# role = employee
# department = General
#
# =========================================================

class UserRegister(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )


# =========================================================
# ADMIN USER CREATION
# =========================================================
#
# Used by:
# POST /users/
#
# Only an administrator can use this endpoint.
#
# Admin can select:
# - name
# - email
# - password
# - role
# - department
#
# =========================================================

class AdminUserCreate(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    role: str = Field(
        default="employee",
        min_length=1,
        max_length=50,
    )

    department: str = Field(
        default="General",
        min_length=1,
        max_length=100,
    )


# =========================================================
# USER RESPONSE
# =========================================================
#
# Returned to frontend.
#
# =========================================================

class UserResponse(BaseModel):

    id: int

    name: str

    email: EmailStr

    role: str

    department: str

    is_active: bool

    class Config:
        from_attributes = True


# =========================================================
# LOGIN TOKEN RESPONSE
# =========================================================

class TokenResponse(BaseModel):

    access_token: str

    token_type: str

    user: UserResponse


# =========================================================
# UPDATE USER ROLE
# =========================================================
#
# Admin only.
#
# =========================================================

class UserRoleUpdate(BaseModel):

    role: str = Field(
        min_length=1,
        max_length=50,
    )


# =========================================================
# UPDATE USER DEPARTMENT
# =========================================================
#
# Admin only.
#
# =========================================================

class UserDepartmentUpdate(BaseModel):

    department: str = Field(
        min_length=1,
        max_length=100,
    )


# =========================================================
# UPDATE USER STATUS
# =========================================================
#
# Used for:
#
# Pause:
# is_active = False
#
# Resume:
# is_active = True
#
# =========================================================

class UserStatusUpdate(BaseModel):

    is_active: bool

# =========================================================
# PASSWORD MANAGEMENT
# =========================================================

from pydantic import BaseModel, Field, model_validator


class ChangePasswordRequest(BaseModel):

    current_password: str = Field(
        min_length=1,
        max_length=255,
    )

    new_password: str = Field(
        min_length=8,
        max_length=255,
    )

    confirm_password: str = Field(
        min_length=8,
        max_length=255,
    )

    @model_validator(mode="after")
    def validate_passwords(self):

        if self.new_password != self.confirm_password:
            raise ValueError(
                "New passwords do not match."
            )

        if self.current_password == self.new_password:
            raise ValueError(
                "New password must be different from the current password."
            )

        return self


class AdminResetPasswordRequest(BaseModel):

    new_password: str = Field(
        min_length=8,
        max_length=255,
    )

    confirm_password: str = Field(
        min_length=8,
        max_length=255,
    )

    @model_validator(mode="after")
    def validate_passwords(self):

        if self.new_password != self.confirm_password:
            raise ValueError(
                "Passwords do not match."
            )

        return self    