from sqlalchemy.orm import Session

from app.ai.embeddings.embedding_service import (
    get_embedding_service,
)

from app.ai.vectorstore.chroma_store import (
    get_vector_store,
)

from app.models.document import Document

from app.models.document_chunk import (
    DocumentChunk,
)


# ============================================================
# INDEX DOCUMENT
# ============================================================

def index_document(
    document: Document,
    db: Session,
) -> int:

    """
    Convert document chunks into embeddings
    and store them in ChromaDB.

    Returns the number of indexed chunks.
    """

    # --------------------------------------------------------
    # 1. LOAD DOCUMENT CHUNKS
    # --------------------------------------------------------

    chunks = (
        db.query(DocumentChunk)
        .filter(
            DocumentChunk.document_id
            == document.id
        )
        .order_by(
            DocumentChunk.page_number,
            DocumentChunk.chunk_index,
        )
        .all()
    )


    if not chunks:

        raise ValueError(
            "Document has no chunks. "
            "Process the document first."
        )


    # --------------------------------------------------------
    # 2. PREPARE CHUNK TEXT
    # --------------------------------------------------------

    texts = [
        chunk.content
        for chunk in chunks
    ]


    # --------------------------------------------------------
    # 3. GENERATE EMBEDDINGS
    # --------------------------------------------------------

    embedding_service = (
        get_embedding_service()
    )


    embeddings = (
        embedding_service
        .embed_documents(
            texts
        )
    )


    if not embeddings:

        raise ValueError(
            "Unable to generate embeddings "
            "for document chunks."
        )


    if (
        len(embeddings)
        != len(chunks)
    ):

        raise ValueError(
            "Embedding count does not match "
            "document chunk count."
        )


    # --------------------------------------------------------
    # 4. GET VECTOR STORE
    # --------------------------------------------------------

    vector_store = (
        get_vector_store()
    )


    # --------------------------------------------------------
    # 5. CREATE UNIQUE VECTOR IDS
    # --------------------------------------------------------

    ids = [
        f"chunk-{chunk.id}"
        for chunk in chunks
    ]


    # --------------------------------------------------------
    # 6. CREATE CHROMA METADATA
    # --------------------------------------------------------

    metadatas: list[dict] = []


    for chunk in chunks:

        metadata = {

            # Document identity

            "document_id":
                int(document.id),

            "document_name":
                str(document.name),


            # Chunk identity

            "chunk_id":
                int(chunk.id),

            "chunk_index":
                int(chunk.chunk_index),


            # Source location

            "page_number":
                int(chunk.page_number),


            # Enterprise metadata

            "department":
                str(document.department),

            "version":
                str(document.version),

            "status":
                str(document.status),

        }


        # ----------------------------------------------------
        # OPTIONAL SECURITY METADATA
        # ----------------------------------------------------

        # Chroma metadata does not accept None values
        # consistently across versions, so only store
        # optional values when they exist.

        if document.access_level:

            metadata[
                "access_level"
            ] = str(
                document.access_level
            )


        if document.project_name:

            metadata[
                "project_name"
            ] = str(
                document.project_name
            )


        if document.owner_id is not None:

            metadata[
                "owner_id"
            ] = int(
                document.owner_id
            )


        # ----------------------------------------------------
        # SEARCH WEIGHT
        # ----------------------------------------------------

        if document.search_weight is not None:

            metadata[
                "search_weight"
            ] = float(
                document.search_weight
            )


        metadatas.append(
            metadata
        )


    # --------------------------------------------------------
    # 7. REMOVE OLD VECTORS
    # --------------------------------------------------------

    # This allows a document to be safely
    # re-indexed without leaving duplicate
    # vectors in ChromaDB.

    vector_store.delete_document(
        document.id
    )


    # --------------------------------------------------------
    # 8. STORE NEW VECTORS
    # --------------------------------------------------------

    vector_store.add_chunks(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )


    # --------------------------------------------------------
    # 9. RETURN INDEXED CHUNK COUNT
    # --------------------------------------------------------

    return len(chunks)