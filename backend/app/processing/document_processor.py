from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import (
    DocumentChunk,
)
from app.processing.chunker import (
    chunk_text,
)
from app.processing.pdf_extractor import (
    extract_pdf_pages,
)


def process_document(
    document: Document,
    db: Session,
) -> int:

    pages = extract_pdf_pages(
        document.file_path
    )

    if not pages:
        raise ValueError(
            "No readable text was found "
            "inside this PDF."
        )

    # Allows safe reprocessing later.
    db.query(DocumentChunk).filter(
        DocumentChunk.document_id
        == document.id
    ).delete(
        synchronize_session=False
    )

    total_chunks = 0

    try:
        for page in pages:

            chunks = chunk_text(
                page["text"]
            )

            for chunk_index, content in enumerate(
                chunks
            ):

                document_chunk = (
                    DocumentChunk(
                        document_id=
                            document.id,

                        page_number=
                            page[
                                "page_number"
                            ],

                        chunk_index=
                            chunk_index,

                        content=
                            content,

                        character_count=
                            len(content),
                    )
                )

                db.add(
                    document_chunk
                )

                total_chunks += 1

        db.commit()

    except Exception:
        db.rollback()
        raise

    return total_chunks