from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.retrieval import (
    RetrievalRequest,
    search_knowledge,
)

from app.auth.dependencies import (
    get_current_user,
)

from app.database.database import (
    get_db,
)

from app.models.user import User

from app.ai.llm_service import (
    generate_answer,
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/ask",
    tags=["AI Answer"],
)


# =========================================================
# REQUEST
# =========================================================

class AskRequest(BaseModel):

    query: str = Field(
        min_length=2,
        max_length=1000,
    )


# =========================================================
# SOURCE
# =========================================================

class AnswerSource(BaseModel):

    document_name: str

    version: str

    page_number: int | None = None


# =========================================================
# RESPONSE
# =========================================================

class AskResponse(BaseModel):

    answer: str

    confidence: str

    sources: list[AnswerSource]


# =========================================================
# ASK
# =========================================================

@router.post(
    "",
    response_model=AskResponse,
)
def ask_knowledge(

    request: AskRequest,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),

):

    # -----------------------------------------------------
    # 1. Clean question
    # -----------------------------------------------------

    query = request.query.strip()

    if not query:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )


    # -----------------------------------------------------
    # 2. Retrieve knowledge
    # -----------------------------------------------------

    retrieval_request = RetrievalRequest(
        query=query,
        limit=6,
    )

    retrieval_response = search_knowledge(
        request=retrieval_request,
        db=db,
        current_user=current_user,
    )


    # -----------------------------------------------------
    # 3. Keep ONLY trusted + latest documents
    # -----------------------------------------------------

    trusted_results = [

        result

        for result
        in retrieval_response.results

        if (
            result.trusted
            and result.is_latest_version
        )

    ]


    # -----------------------------------------------------
    # 4. No authoritative knowledge
    # -----------------------------------------------------

    if not trusted_results:

        return AskResponse(
            answer=(
                "I couldn't find that information "
                "in the approved enterprise knowledge base."
            ),
            confidence="low",
            sources=[],
        )


    # -----------------------------------------------------
    # 4A. Relevance check
    # -----------------------------------------------------

    RELEVANCE_THRESHOLD = 0.25

    relevant_results = [
        result
        for result in trusted_results
        if result.similarity_score >= RELEVANCE_THRESHOLD
    ]


    if not relevant_results:

        return AskResponse(
            answer=(
                "I couldn't find that information "
                "in the approved enterprise knowledge base."
            ),
            confidence="low",
            sources=[],
        )


    trusted_results = relevant_results

    # -----------------------------------------------------
    # 5. Rank strongest evidence
    # -----------------------------------------------------

    trusted_results.sort(

        key=lambda result: (
            result.evidence_score,
            result.similarity_score,
        ),

        reverse=True,
    )


    # -----------------------------------------------------
    # 6. Remove duplicate evidence
    # -----------------------------------------------------

    unique_results = []

    seen = set()


    for result in trusted_results:

        key = (
            result.document_name,
            result.version,
            result.page_number,
            result.chunk_index,
        )


        if key in seen:

            continue


        seen.add(key)

        unique_results.append(
            result
        )


    # -----------------------------------------------------
    # Keep strongest 4 pieces of evidence
    # -----------------------------------------------------

    evidence_results = unique_results[:4]


    # -----------------------------------------------------
    # 7. Calculate confidence
    # -----------------------------------------------------

    best_result = evidence_results[0]


    if best_result.evidence_score >= 0.75:

        confidence = "high"

    elif best_result.evidence_score >= 0.55:

        confidence = "medium"

    else:

        confidence = "low"


    # -----------------------------------------------------
    # 8. Build grounded context
    # -----------------------------------------------------

    context_parts = []


    for index, result in enumerate(
        evidence_results,
        start=1,
    ):

        context_parts.append(

            f"""
SOURCE {index}

Document:
{result.document_name}

Version:
{result.version}

Page:
{result.page_number}

Content:
{result.content}
""".strip()

        )


    context = "\n\n--------------------\n\n".join(
        context_parts
    )


    # -----------------------------------------------------
    # 9. Generate LOCAL AI answer
    # -----------------------------------------------------

    try:

        answer = generate_answer(
            question=query,
            context=context,
        )
        # -----------------------------------------------------
        # 9A. Unsupported / unanswered question
        # -----------------------------------------------------

        normalized_answer = answer.strip().lower()

        unsupported_phrases = [
            "i couldn't find that information",
            "i could not find that information",
            "i couldn't find enough information",
            "i could not find enough information",
        ]

        if any(
            phrase in normalized_answer
            for phrase in unsupported_phrases
        ):

            return AskResponse(
                answer=(
                    "I couldn't find that information "
                    "in the approved enterprise knowledge base."
                ),
                confidence="low",
                sources=[],
            )

    except Exception as exc:

        print(
            "Local AI answer generation failed:",
            exc,
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "The local AI answer service "
                "could not generate a response."
            ),
        )


    # -----------------------------------------------------
    # 10. Build clean sources
    # -----------------------------------------------------

    sources = []


    for result in evidence_results:

        source = AnswerSource(

            document_name=(
                result.document_name
            ),

            version=(
                result.version
            ),

            page_number=(
                result.page_number
            ),
        )


        # Avoid duplicate sources

        already_exists = any(

            existing.document_name
            == source.document_name

            and existing.version
            == source.version

            and existing.page_number
            == source.page_number

            for existing
            in sources

        )


        if not already_exists:

            sources.append(
                source
            )


    # -----------------------------------------------------
    # 11. Return clean answer
    # -----------------------------------------------------

    return AskResponse(

        answer=answer,

        confidence=confidence,

        sources=sources,
    )