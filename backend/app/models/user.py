from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    # =========================================================
    # PRIMARY KEY
    # =========================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # =========================================================
    # BASIC INFORMATION
    # =========================================================

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # =========================================================
    # ROLE
    # =========================================================
    #
    # Supported roles:
    #
    # admin
    # ceo
    # knowledge_manager
    # hr
    # tl
    # employee
    # guest
    #
    # =========================================================

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="employee",
        index=True,
    )

    # =========================================================
    # DEPARTMENT
    # =========================================================

    department: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="General",
        index=True,
    )

    # =========================================================
    # ACCOUNT STATUS
    # =========================================================

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
    )

    # =========================================================
    # CREATED AT
    # =========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # =========================================================
    # DOCUMENTS UPLOADED BY USER
    # =========================================================

    documents = relationship(
        "Document",
        back_populates="uploader",
        foreign_keys="Document.uploaded_by",
    )