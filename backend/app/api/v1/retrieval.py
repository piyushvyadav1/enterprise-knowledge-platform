from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from pydantic import BaseModel, Field

from sqlalchemy.orm import Session

from app.ai.embeddings.embedding_service import (
    get_embedding_service,
)

from app.ai.vectorstore.chroma_store import (
    get_vector_store,
)

from app.ai.validation.knowledge_validator import (
    validate_document,
)

from app.auth.dependencies import (
    get_current_user,
)

from app.database.database import (
    get_db,
)

from app.models.document import (
    Document,
)

from app.models.document_chunk import (
    DocumentChunk,
)

from app.models.user import (
    User,
)

from app.security.document_access import (
    can_access_document,
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/retrieval",
    tags=["Retrieval"],
)


# =========================================================
# REQUEST SCHEMA
# =========================================================

class RetrievalRequest(BaseModel):

    query: str = Field(
        min_length=2,
        max_length=1000,
    )

    limit: int = Field(
        default=5,
        ge=1,
        le=10,
    )


# =========================================================
# RESULT SCHEMA
# =========================================================

class RetrievalResult(BaseModel):

    # -----------------------------------------------------
    # Document information
    # -----------------------------------------------------

    document_id: int

    document_name: str


    # -----------------------------------------------------
    # Chunk information
    # -----------------------------------------------------

    page_number: int | None = None

    chunk_index: int | None = None


    # -----------------------------------------------------
    # Content
    # -----------------------------------------------------

    content: str


    # -----------------------------------------------------
    # Semantic similarity
    # -----------------------------------------------------

    distance: float

    similarity_score: float


    # -----------------------------------------------------
    # Enterprise evidence ranking
    # -----------------------------------------------------

    evidence_score: float


    # -----------------------------------------------------
    # Enterprise metadata
    # -----------------------------------------------------

    version: str

    status: str

    department: str

    access_level: str


    # -----------------------------------------------------
    # Knowledge validation
    # -----------------------------------------------------

    trusted: bool

    trust_score: float

    validation_reason: str


    # -----------------------------------------------------
    # Version validation
    # -----------------------------------------------------

    is_latest_version: bool

    newer_version_id: int | None = None

    newer_version: str | None = None


# =========================================================
# RESPONSE SCHEMA
# =========================================================

class RetrievalResponse(BaseModel):

    query: str

    result_count: int

    results: list[RetrievalResult]


# =========================================================
# SEMANTIC SEARCH ENDPOINT
# =========================================================

@router.post(
    "/search",
    response_model=RetrievalResponse,
)
def search_knowledge(

    request: RetrievalRequest,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),

):

    # =====================================================
    # 1. CLEAN AND VALIDATE QUERY
    # =====================================================

    query = request.query.strip()


    if not query:

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),

            detail=(
                "Query cannot be empty"
            ),
        )


    # =====================================================
    # 2. LOAD AI SERVICES
    # =====================================================

    embedding_service = (
        get_embedding_service()
    )


    vector_store = (
        get_vector_store()
    )


    # =====================================================
    # 3. GENERATE QUERY EMBEDDING
    # =====================================================

    try:

        query_embedding = (
            embedding_service.embed_query(
                query
            )
        )

    except Exception as exc:

        raise HTTPException(

            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),

            detail=(
                "Failed to generate "
                "query embedding: "
                f"{str(exc)}"
            ),

        )


    # =====================================================
    # 4. SEARCH CHROMADB
    # =====================================================

    try:

        # -------------------------------------------------
        # IMPORTANT:
        #
        # Retrieve MORE candidates than the user requested.
        #
        # We cannot stop at request.limit because an older
        # document may appear before a newer trusted version.
        #
        # We need enough candidates to perform:
        #
        # Chroma search
        #       ↓
        # Permission filtering
        #       ↓
        # Version validation
        #       ↓
        # Evidence ranking
        #       ↓
        # Final limit
        # -------------------------------------------------

        candidate_limit = min(
            max(
                request.limit * 4,
                20,
            ),
            40,
        )


        raw_results = (
            vector_store.search(
                query_embedding=(
                    query_embedding
                ),

                limit=(
                    candidate_limit
                ),
            )
        )

    except Exception as exc:

        raise HTTPException(

            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),

            detail=(
                "Vector search failed: "
                f"{str(exc)}"
            ),

        )


    # =====================================================
    # 5. EXTRACT CHROMA RESULT ARRAYS
    # =====================================================

    chroma_documents = (
        raw_results.get(
            "documents"
        )
        or [[]]
    )


    chroma_metadatas = (
        raw_results.get(
            "metadatas"
        )
        or [[]]
    )


    chroma_distances = (
        raw_results.get(
            "distances"
        )
        or [[]]
    )


    retrieved_documents = (

        chroma_documents[0]

        if chroma_documents

        else []

    )


    retrieved_metadatas = (

        chroma_metadatas[0]

        if chroma_metadatas

        else []

    )


    retrieved_distances = (

        chroma_distances[0]

        if chroma_distances

        else []

    )


    # =====================================================
    # 6. BUILD SECURE RETRIEVAL RESULTS
    # =====================================================

    results: list[
        RetrievalResult
    ] = []


    # =====================================================
    # IMPORTANT:
    #
    # There is NO "break" inside this loop.
    #
    # We must evaluate ALL candidates first.
    # =====================================================

    for (
        content,
        metadata,
        distance,
    ) in zip(

        retrieved_documents,

        retrieved_metadatas,

        retrieved_distances,

    ):


        # =================================================
        # 6.1 METADATA MUST EXIST
        # =================================================

        if not metadata:

            continue


        # =================================================
        # 6.2 GET POSTGRESQL DOCUMENT ID
        # =================================================

        document_id = (
            metadata.get(
                "document_id"
            )
        )


        if document_id is None:

            continue


        try:

            document_id = int(
                document_id
            )

        except (
            TypeError,
            ValueError,
        ):

            continue


        # =================================================
        # 6.3 LOAD REAL DOCUMENT FROM POSTGRESQL
        # =================================================

        document = (

            db.query(
                Document
            )

            .filter(
                Document.id
                == document_id
            )

            .first()

        )


        # -------------------------------------------------
        # Never return orphaned Chroma vectors.
        # -------------------------------------------------

        if document is None:

            continue


        # =================================================
        # 6.4 SECURITY CHECK
        # =================================================

        decision = can_access_document(
            current_user,
            document,
        )

        if not decision:
            continue


        # =================================================
        # 6.5 KNOWLEDGE VALIDATION
        # =================================================

        validation = (
            validate_document(
                document,
                db,
            )
        )


        # =================================================
        # 6.6 SIMILARITY CALCULATION
        # =================================================

        numeric_distance = float(
            distance
        )


        # -------------------------------------------------
        # Chroma collection uses cosine distance.
        #
        # Smaller distance = better match.
        #
        # Convert:
        #
        # distance → similarity
        #
        # into a 0-1 score.
        # -------------------------------------------------

        similarity_score = max(

            0.0,

            min(

                1.0,

                1.0
                - numeric_distance,

            ),

        )


        # =================================================
        # 6.7 TRUST SCORE
        # =================================================

        trust_score = max(

            0.0,

            min(

                1.0,

                float(
                    validation.trust_score
                ),

            ),

        )


        # =================================================
        # 6.8 LATEST VERSION SCORE
        # =================================================

        latest_score = (

            1.0

            if validation.is_latest_version

            else 0.0

        )


        # =================================================
        # 6.9 ENTERPRISE EVIDENCE SCORE
        # =================================================
        #
        # Weighting:
        #
        # Semantic relevance   60%
        # Trust                 30%
        # Latest version       10%
        #
        # This prevents a superseded document from
        # outranking a trusted current document simply
        # because its embedding happened to be slightly
        # closer to the query.
        # =================================================

        evidence_score = (

            similarity_score
            * 0.60

            +

            trust_score
            * 0.30

            +

            latest_score
            * 0.10

        )


        evidence_score = round(

            evidence_score,

            6,

        )


        # =================================================
        # 6.10 RESOLVE AUTHORITATIVE CHUNK METADATA
        # =================================================

        page_number = None

        chunk_index = None


        chunk_id = (
            metadata.get(
                "chunk_id"
            )
        )


        # =================================================
        # 6.11 PREFER POSTGRESQL CHUNK METADATA
        # =================================================

        if chunk_id is not None:

            try:

                chunk_id = int(
                    chunk_id
                )


                chunk = (

                    db.query(
                        DocumentChunk
                    )

                    .filter(

                        DocumentChunk.id
                        == chunk_id,

                        DocumentChunk.document_id
                        == document.id,

                    )

                    .first()

                )


                if chunk is not None:

                    page_number = (
                        chunk.page_number
                    )

                    chunk_index = (
                        chunk.chunk_index
                    )


            except (
                TypeError,
                ValueError,
            ):

                chunk_id = None


        # =================================================
        # 6.12 FALLBACK TO CHROMA PAGE NUMBER
        # =================================================

        if page_number is None:

            metadata_page_number = (

                metadata.get(
                    "page_number"
                )

            )


            try:

                if (
                    metadata_page_number
                    is not None
                ):

                    page_number = int(
                        metadata_page_number
                    )


            except (
                TypeError,
                ValueError,
            ):

                page_number = None


        # =================================================
        # 6.13 FALLBACK TO CHROMA CHUNK INDEX
        # =================================================

        if chunk_index is None:

            metadata_chunk_index = (

                metadata.get(
                    "chunk_index"
                )

            )


            try:

                if (
                    metadata_chunk_index
                    is not None
                ):

                    chunk_index = int(
                        metadata_chunk_index
                    )


            except (
                TypeError,
                ValueError,
            ):

                chunk_index = None


        # =================================================
        # 6.14 ADD RESULT
        # =================================================

        results.append(

            RetrievalResult(

                # -----------------------------------------
                # Document
                # -----------------------------------------

                document_id=(
                    document.id
                ),

                document_name=(
                    document.name
                ),


                # -----------------------------------------
                # Chunk
                # -----------------------------------------

                page_number=(
                    page_number
                ),

                chunk_index=(
                    chunk_index
                ),


                # -----------------------------------------
                # Content
                # -----------------------------------------

                content=(
                    content or ""
                ),


                # -----------------------------------------
                # Similarity
                # -----------------------------------------

                distance=(
                    numeric_distance
                ),

                similarity_score=(
                    similarity_score
                ),


                # -----------------------------------------
                # Evidence
                # -----------------------------------------

                evidence_score=(
                    evidence_score
                ),


                # -----------------------------------------
                # Enterprise metadata
                # -----------------------------------------

                version=(
                    document.version
                ),

                status=(
                    document.status
                ),

                department=(
                    document.department
                ),

                access_level=(
                    document.access_level
                ),


                # -----------------------------------------
                # Validation
                # -----------------------------------------

                trusted=(
                    validation.trusted
                ),

                trust_score=(
                    validation.trust_score
                ),

                validation_reason=(
                    validation.reason
                ),


                # -----------------------------------------
                # Version
                # -----------------------------------------

                is_latest_version=(
                    validation.is_latest_version
                ),

                newer_version_id=(
                    validation.newer_version_id
                ),

                newer_version=(
                    validation.newer_version
                ),

            )

        )


    # =====================================================
    # 7. RANK ALL RESULTS
    # =====================================================
    #
    # THIS MUST HAPPEN AFTER THE LOOP.
    #
    # We intentionally do NOT apply request.limit before
    # this point.
    # =====================================================

    results = sorted(

        results,

        key=lambda item: (

            item.evidence_score,

            item.trust_score,

            item.is_latest_version,

            item.similarity_score,

        ),

        reverse=True,

    )


    # =====================================================
    # 8. APPLY FINAL RESULT LIMIT
    # =====================================================
    #
    # Only NOW do we apply request.limit.
    # =====================================================

    results = results[
        :request.limit
    ]


    # =====================================================
    # 9. RETURN RESPONSE
    # =====================================================

    return RetrievalResponse(

        query=query,

        result_count=len(
            results
        ),

        results=results,

    )