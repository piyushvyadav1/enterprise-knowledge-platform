from sqlalchemy.orm import Query
from sqlalchemy import func, or_

from app.models.document import Document
from app.models.user import User


# =========================================================
# ROLE DEFINITIONS
# =========================================================

ADMIN_ROLES = {
    "admin",
    "knowledge_manager",
    "ceo",
}


MANAGEMENT_ROLES = {
    "admin",
    "knowledge_manager",
    "ceo",
    "hr",
    "tl",
}


# =========================================================
# NORMALIZATION
# =========================================================

def normalize(value: str | None) -> str:
    if not value:
        return ""

    return value.strip().lower()


def normalize_departments(value: str | None) -> list[str]:
    """
    Converts:

        HR
        HR,Sales
        HR, Sales
        hr, sales

    into:

        ["hr"]
        ["hr", "sales"]
        ["hr", "sales"]
        ["hr", "sales"]
    """

    if not value:
        return []

    return [
        department.strip().lower()
        for department in value.split(",")
        if department.strip()
    ]


# =========================================================
# DOCUMENT ACCESS CHECK
# =========================================================

def can_access_document(
    user: User,
    document: Document,
) -> bool:

    if user is None:
        return False

    if document is None:
        return False

    role = normalize(user.role)

    user_departments = normalize_departments(
        user.department
    )

    document_departments = normalize_departments(
        document.department
    )

    access_level = normalize(
        document.access_level
    )

    # -----------------------------------------------------
    # ADMIN / KNOWLEDGE MANAGER / CEO
    # -----------------------------------------------------

    if role in ADMIN_ROLES:
        return True

    # -----------------------------------------------------
    # PUBLIC
    # -----------------------------------------------------

    if access_level == "public":
        return True

    # -----------------------------------------------------
    # COMPANY-WIDE
    # -----------------------------------------------------

    if access_level in {
        "company",
        "company-wide",
        "global",
        "all",
    }:
        return True

    # -----------------------------------------------------
    # PRIVATE
    # -----------------------------------------------------

    if access_level == "private":

        if document.owner_id == user.id:
            return True

        if document.uploaded_by == user.id:
            return True

        return False

    # -----------------------------------------------------
    # DEPARTMENT
    # -----------------------------------------------------

    if access_level == "department":

        if not user_departments:
            return False

        if not document_departments:
            return False

        # ANY matching department gives access
        return bool(
            set(user_departments)
            & set(document_departments)
        )

    # -----------------------------------------------------
    # DEFAULT
    # -----------------------------------------------------

    # Unknown access levels are denied.
    return False


# =========================================================
# SQL QUERY FILTER
# =========================================================

def apply_document_access_filter(
    query: Query,
    user: User,
) -> Query:

    role = normalize(user.role)

    user_departments = normalize_departments(
        user.department
    )

    # -----------------------------------------------------
    # ADMIN / KNOWLEDGE MANAGER / CEO
    # -----------------------------------------------------

    if role in ADMIN_ROLES:
        return query

    # -----------------------------------------------------
    # PUBLIC / COMPANY-WIDE
    # -----------------------------------------------------

    public_filter = (
        Document.access_level.in_(
            [
                "public",
                "company",
                "company-wide",
                "global",
                "all",
            ]
        )
    )

    # -----------------------------------------------------
    # DEPARTMENT FILTER
    # -----------------------------------------------------

    department_filters = []

    for department in user_departments:

        department = department.lower().strip()

        if not department:
            continue

        # Supports:
        #
        # Sales
        # Sales,HR
        # HR,Sales
        # Sales,HR,Marketing

        department_filters.append(
            or_(
                func.lower(
                    Document.department
                ) == department,

                func.lower(
                    Document.department
                ).like(
                    f"{department},%"
                ),

                func.lower(
                    Document.department
                ).like(
                    f"%,{department}"
                ),

                func.lower(
                    Document.department
                ).like(
                    f"%,{department},%"
                ),
            )
        )

    if department_filters:

        department_filter = or_(
            *department_filters
        )

        department_access = (
            (Document.access_level == "department")
            &
            department_filter
        )

    else:

        department_access = False

    # -----------------------------------------------------
    # PRIVATE DOCUMENTS
    # -----------------------------------------------------

    private_access = (
        (Document.access_level == "private")
        &
        (
            (Document.owner_id == user.id)
            |
            (Document.uploaded_by == user.id)
        )
    )

    # -----------------------------------------------------
    # FINAL SECURITY FILTER
    # -----------------------------------------------------

    return query.filter(
        public_filter
        |
        department_access
        |
        private_access
    )