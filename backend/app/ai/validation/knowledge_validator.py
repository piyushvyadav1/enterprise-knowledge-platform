from dataclasses import dataclass
import re

from sqlalchemy.orm import Session

from app.models.document import Document


# ============================================================
# TRUSTED / UNTRUSTED KNOWLEDGE STATUSES
# ============================================================

TRUSTED_STATUSES = {
    "approved",
    "published",
    "active",
}

UNTRUSTED_STATUSES = {
    "draft",
    "rejected",
    "archived",
    "deprecated",
}


# ============================================================
# VALIDATION RESULT
# ============================================================

@dataclass
class ValidationResult:

    trusted: bool
    trust_score: float
    status: str
    reason: str

    is_latest_version: bool

    newer_version_id: int | None = None
    newer_version: str | None = None


# ============================================================
# VERSION PARSER
# ============================================================

def _version_tuple(
    version: str,
) -> tuple:
    """
    Convert versions such as:

    1
    1.0
    1.2
    2
    2.0
    2.1.3

    into sortable tuples.
    """

    try:

        parts = str(
            version
        ).strip().split(".")

        return tuple(
            int(part)
            for part in parts
        )

    except (
        TypeError,
        ValueError,
    ):

        return (0,)


# ============================================================
# NORMALIZE DOCUMENT NAME
# ============================================================

def _normalize_name(
    name: str | None,
) -> str:
    """
    Normalize document names so minor differences
    do not automatically create a new document family.

    Examples:

    Employee Leave Policy
        ->
    employee leave policy

    employee-leave-policy
        ->
    employee leave policy

    Employee_Leave_Policy
        ->
    employee leave policy
    """

    if not name:
        return ""

    value = str(
        name
    ).strip().lower()

    # Remove file extension if one exists.

    value = re.sub(
        r"\.(pdf|docx?|txt)$",
        "",
        value,
    )

    # Replace separators with spaces.

    value = re.sub(
        r"[_\-]+",
        " ",
        value,
    )

    # Remove punctuation.

    value = re.sub(
        r"[^a-z0-9\s]",
        " ",
        value,
    )

    # Collapse repeated spaces.

    value = re.sub(
        r"\s+",
        " ",
        value,
    ).strip()

    return value


# ============================================================
# DOCUMENT FAMILY TOKENS
# ============================================================

def _family_tokens(
    name: str | None,
) -> set[str]:

    normalized = _normalize_name(
        name
    )

    if not normalized:
        return set()

    # Words that usually do not define the actual
    # document family.

    ignored_words = {
        "document",
        "file",
        "test",
        "draft",
        "final",
        "updated",
        "update",
        "copy",
        "version",
        "v1",
        "v2",
        "v3",
    }

    return {
        word
        for word in normalized.split()
        if (
            word
            and word not in ignored_words
        )
    }


# ============================================================
# DOCUMENT FAMILY MATCHING
# ============================================================

def _same_document_family(
    first: Document,
    second: Document,
) -> bool:
    """
    Determine whether two database documents are
    probably versions of the same logical document.

    This is intentionally conservative.
    """

    # --------------------------------------------------------
    # Department must match
    # --------------------------------------------------------

    first_department = (
        first.department or ""
    ).strip().lower()

    second_department = (
        second.department or ""
    ).strip().lower()


    if (
        first_department
        != second_department
    ):

        return False


    # --------------------------------------------------------
    # Exact normalized name match
    # --------------------------------------------------------

    first_name = _normalize_name(
        first.name
    )

    second_name = _normalize_name(
        second.name
    )


    if (
        first_name
        and
        first_name == second_name
    ):

        return True


    # --------------------------------------------------------
    # Compare meaningful words
    # --------------------------------------------------------

    first_tokens = _family_tokens(
        first.name
    )

    second_tokens = _family_tokens(
        second.name
    )


    if (
        not first_tokens
        or
        not second_tokens
    ):

        return False


    common_tokens = (
        first_tokens
        & second_tokens
    )


    # --------------------------------------------------------
    # Strong overlap rule
    # --------------------------------------------------------

    smaller_token_count = min(
        len(first_tokens),
        len(second_tokens),
    )


    overlap_ratio = (
        len(common_tokens)
        /
        smaller_token_count
    )


    # Require at least one meaningful common word
    # AND strong overlap with the smaller name.

    if (
        len(common_tokens) >= 1
        and
        overlap_ratio >= 0.60
    ):

        return True


    return False


# ============================================================
# VALIDATE DOCUMENT
# ============================================================

def validate_document(
    document: Document,
    db: Session,
) -> ValidationResult:

    status = (
        document.status
        or "unknown"
    ).strip().lower()


    # ========================================================
    # 1. FIND POSSIBLE RELATED DOCUMENTS
    # ========================================================

    possible_documents = (
        db.query(Document)
        .filter(
            Document.id
            != document.id,

            Document.department
            == document.department,
        )
        .all()
    )


    # ========================================================
    # 2. IDENTIFY SAME DOCUMENT FAMILY
    # ========================================================

    related_documents = []

    for candidate in possible_documents:

        if _same_document_family(
            document,
            candidate,
        ):

            related_documents.append(
                candidate
            )


    # ========================================================
    # 3. DETERMINE CURRENT VERSION
    # ========================================================

    current_version = (
        _version_tuple(
            document.version
        )
    )


    # ========================================================
    # 4. FIND NEWER VERSIONS
    # ========================================================

    newer_documents = []


    for candidate in related_documents:

        candidate_version = (
            _version_tuple(
                candidate.version
            )
        )


        if (
            candidate_version
            > current_version
        ):

            newer_documents.append(
                candidate
            )


    # ========================================================
    # 5. SELECT NEWEST VERSION
    # ========================================================

    newer_document = None


    if newer_documents:

        newer_document = max(
            newer_documents,
            key=lambda item:
                _version_tuple(
                    item.version
                ),
        )


    is_latest_version = (
        newer_document is None
    )


    # ========================================================
    # 6. BASE STATUS VALIDATION
    # ========================================================

    if status in TRUSTED_STATUSES:

        trusted = True

        trust_score = 1.0

        reason = (
            "Document has an approved "
            "knowledge status."
        )


    elif status == "draft":

        trusted = False

        trust_score = 0.35

        reason = (
            "Document is a draft and must "
            "not be treated as authoritative "
            "enterprise knowledge."
        )


    elif status in {
        "archived",
        "deprecated",
    }:

        trusted = False

        trust_score = 0.10

        reason = (
            "Document is no longer considered "
            "current enterprise knowledge."
        )


    elif status == "rejected":

        trusted = False

        trust_score = 0.0

        reason = (
            "Document has been rejected."
        )


    else:

        trusted = False

        trust_score = 0.20

        reason = (
            "Document does not have a "
            "recognized trusted status."
        )


    # ========================================================
    # 7. VERSION VALIDATION
    # ========================================================

    if newer_document is not None:

        trusted = False

        trust_score = min(
            trust_score,
            0.25,
        )


        reason += (
            f" A newer version "
            f"({newer_document.version}) exists."
        )


    # ========================================================
    # 8. FINAL RESULT
    # ========================================================

    return ValidationResult(

        trusted=trusted,

        trust_score=trust_score,

        status=status,

        reason=reason,

        is_latest_version=(
            is_latest_version
        ),

        newer_version_id=(
            newer_document.id
            if newer_document
            else None
        ),

        newer_version=(
            newer_document.version
            if newer_document
            else None
        ),
    )