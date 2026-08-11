from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database.database import Base


class Document(Base):
    __tablename__ = "documents"

    # =========================================================
    # CORE
    # =========================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    stored_filename: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    # =========================================================
    # DEPARTMENT
    # =========================================================

    department: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    # =========================================================
    # VERSION / STATUS
    # =========================================================

    version: Mapped[str] = mapped_column(
        String(50),
        default="1.0",
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="draft",
        nullable=False,
        index=True,
    )

    # =========================================================
    # FILE
    # =========================================================

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    page_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    checksum: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    # =========================================================
    # UPLOAD / AUDIT
    # =========================================================

    uploaded_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # =========================================================
    # PROCESSING
    # =========================================================

    processing_status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
    )

    chunk_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # =========================================================
    # INDEXING
    # =========================================================

    indexing_status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
    )

    indexed_chunk_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # =========================================================
    # SECURITY
    # =========================================================
    #
    # public
    # department
    # private
    #
    # =========================================================

    access_level: Mapped[str] = mapped_column(
        String(30),
        default="public",
        nullable=False,
        index=True,
    )

    project_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    search_weight: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
    )

    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    # =========================================================
    # RELATIONSHIPS
    # =========================================================

    uploader = relationship(
        "User",
        back_populates="documents",
        foreign_keys=[uploaded_by],
    )

    owner = relationship(
        "User",
        foreign_keys=[owner_id],
    )