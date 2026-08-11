import hashlib
import uuid
from pathlib import Path

import fitz

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from fastapi.responses import FileResponse

from sqlalchemy.orm import Session

from app.ai.indexing_service import index_document
from app.ai.vectorstore.chroma_store import get_vector_store

from app.auth.dependencies import (
    get_current_user,
    require_roles,
)

from app.database.database import get_db

from app.models.document import Document
from app.models.user import User

from app.processing.document_processor import process_document

from app.schemas.document import DocumentResponse

from app.security.document_access import (
    apply_document_access_filter,
    can_access_document,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[3]

UPLOAD_DIR = BASE_DIR / "uploads"

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# LIMITS
# ============================================================

MAX_FILE_SIZE = 20 * 1024 * 1024


# ============================================================
# HELPERS
# ============================================================

def get_document_or_404(
    document_id: int,
    db: Session,
) -> Document:

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id
        )
        .first()
    )

    if not document:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return document


def validate_document_file(
    document: Document,
) -> Path:

    if not document.file_path:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file path is missing.",
        )

    file_path = Path(
        document.file_path
    ).resolve()

    upload_root = (
        UPLOAD_DIR.resolve()
    )

    # --------------------------------------------------------
    # Security:
    # Make sure the database path cannot escape uploads/
    # --------------------------------------------------------

    try:

        file_path.relative_to(
            upload_root
        )

    except ValueError:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid document file location.",
        )

    # --------------------------------------------------------
    # File must exist
    # --------------------------------------------------------

    if not file_path.exists():

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not found on the server.",
        )

    # --------------------------------------------------------
    # File must actually be a file
    # --------------------------------------------------------

    if not file_path.is_file():

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file is invalid.",
        )

    return file_path


# ============================================================
# UPLOAD DOCUMENT
# ADMIN ONLY
# ============================================================

@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    name: str = Form(...),
    department: str = Form(...),
    version: str = Form("1.0"),
    access_level: str = Form("department"),

    file: UploadFile = File(...),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles([
            "admin",
        ])
    ),
):

    # --------------------------------------------------------
    # Filename
    # --------------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required.",
        )

    # --------------------------------------------------------
    # PDF only
    # --------------------------------------------------------

    if not file.filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents are supported.",
        )

    # --------------------------------------------------------
    # Read file
    # --------------------------------------------------------

    file_bytes = await file.read()

    if not file_bytes:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded document is empty.",
        )

    # --------------------------------------------------------
    # File size
    # --------------------------------------------------------

    if len(file_bytes) > MAX_FILE_SIZE:

        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="PDF exceeds the 20 MB limit.",
        )

    # --------------------------------------------------------
    # PDF signature
    # --------------------------------------------------------

    if not file_bytes.startswith(b"%PDF"):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF file.",
        )

    # --------------------------------------------------------
    # Generate safe server filename
    # --------------------------------------------------------

    unique_filename = (
        f"{uuid.uuid4().hex}.pdf"
    )

    destination = (
        UPLOAD_DIR / unique_filename
    )

    # --------------------------------------------------------
    # Save + validate PDF
    # --------------------------------------------------------

    try:

        destination.write_bytes(
            file_bytes
        )

        pdf = fitz.open(
            destination
        )

        page_count = pdf.page_count

        pdf.close()

    except Exception:

        if destination.exists():

            destination.unlink()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF could not be processed.",
        )

    # --------------------------------------------------------
    # SHA-256 checksum
    # --------------------------------------------------------

    checksum = hashlib.sha256(
        file_bytes
    ).hexdigest()

    # --------------------------------------------------------
    # Create database record
    # --------------------------------------------------------

    document = Document(

        name=name.strip(),

        original_filename=file.filename,

        stored_filename=unique_filename,

        department=department.strip(),

        version=version.strip(),

        status="draft",

        access_level=access_level.strip().lower(),

        file_path=str(
            destination
        ),

        file_size=len(file_bytes),

        page_count=page_count,

        owner_id=current_user.id,

        checksum=checksum,

        uploaded_by=current_user.id,
    )

    # --------------------------------------------------------
    # Save database record
    # --------------------------------------------------------

    try:

        db.add(document)

        db.commit()

        db.refresh(document)

    except Exception:

        db.rollback()

        if destination.exists():

            destination.unlink()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to save document.",
        )

    return document


# ============================================================
# LIST DOCUMENTS
# ACCESS FILTER APPLIED
# ============================================================

@router.get(
    "/",
    response_model=list[DocumentResponse],
)
def list_documents(
    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    # --------------------------------------------------------
    # Start with all documents
    # --------------------------------------------------------

    query = db.query(
        Document
    )

    # --------------------------------------------------------
    # Apply backend access control
    #
    # This prevents unauthorized documents from being
    # returned to the frontend at all.
    # --------------------------------------------------------

    query = apply_document_access_filter(
        query=query,
        user=current_user,
    )

    # --------------------------------------------------------
    # Newest first
    # --------------------------------------------------------

    documents = (
        query
        .order_by(
            Document.uploaded_at.desc()
        )
        .all()
    )

    return documents


# ============================================================
# READ / VIEW PDF
# ============================================================

@router.get(
    "/{document_id}/file",
)
def read_document(
    document_id: int,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    # --------------------------------------------------------
    # 1. Find document
    # --------------------------------------------------------

    document = get_document_or_404(
        document_id=document_id,
        db=db,
    )

    # --------------------------------------------------------
    # 2. SECURITY CHECK
    #
    # Frontend visibility is NOT security.
    #
    # The permission is checked again here.
    # --------------------------------------------------------

    if not can_access_document(
        user=current_user,
        document=document,
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission "
                "to access this document."
            ),
        )

    # --------------------------------------------------------
    # 3. Validate physical file
    # --------------------------------------------------------

    file_path = validate_document_file(
        document
    )

    # --------------------------------------------------------
    # 4. Return PDF inline
    # --------------------------------------------------------

    return FileResponse(
        path=str(file_path),

        media_type="application/pdf",

        filename=document.original_filename,

        content_disposition_type="inline",
    )


# ============================================================
# DELETE DOCUMENT
# ADMIN ONLY
# ============================================================

@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
)
def delete_document(
    document_id: int,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        require_roles([
            "admin",
        ])
    ),
):

    # --------------------------------------------------------
    # 1. Find document
    # --------------------------------------------------------

    document = get_document_or_404(
        document_id=document_id,
        db=db,
    )

    # --------------------------------------------------------
    # 2. Get safe file path
    # --------------------------------------------------------

    file_path = None

    if document.file_path:

        try:

            file_path = validate_document_file(
                document
            )

        except HTTPException as exc:

            # If the physical file is already missing,
            # we can still remove the database record.
            if exc.status_code != status.HTTP_404_NOT_FOUND:

                raise

            file_path = Path(
                document.file_path
            )

    # --------------------------------------------------------
    # 3. Remove vectors
    # --------------------------------------------------------

    try:

        vector_store = get_vector_store()

        vector_store.delete_document(
            document.id
        )

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Unable to remove document "
                f"from search index: {exc}"
            ),
        )

    # --------------------------------------------------------
    # 4. Delete database record
    # --------------------------------------------------------

    try:

        db.delete(
            document
        )

        db.commit()

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Unable to delete document "
                "from database."
            ),
        )

    # --------------------------------------------------------
    # 5. Delete physical PDF
    # --------------------------------------------------------

    file_deleted = False

    try:

        if (
            file_path
            and file_path.exists()
            and file_path.is_file()
        ):

            file_path.unlink()

            file_deleted = True

    except OSError:

        file_deleted = False

    # --------------------------------------------------------
    # 6. Response
    # --------------------------------------------------------

    return {

        "message":
            "Document deleted successfully",

        "document_id":
            document_id,

        "file_deleted":
            file_deleted,

        "search_index_removed":
            True,
    }


# ============================================================
# PROCESS DOCUMENT
# ADMIN + KNOWLEDGE MANAGER
# ============================================================

@router.post(
    "/{document_id}/process",
)
def process_uploaded_document(
    document_id: int,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        require_roles([
            "admin",
            "knowledge_manager",
        ])
    ),
):

    # --------------------------------------------------------
    # Find document
    # --------------------------------------------------------

    document = get_document_or_404(
        document_id=document_id,
        db=db,
    )

    # --------------------------------------------------------
    # Set processing state
    # --------------------------------------------------------

    document.processing_status = (
        "processing"
    )

    db.commit()

    # --------------------------------------------------------
    # Process
    # --------------------------------------------------------

    try:

        chunk_count = process_document(
            document=document,
            db=db,
        )

        document.processing_status = (
            "processed"
        )

        document.chunk_count = (
            chunk_count
        )

        db.commit()

        db.refresh(
            document
        )

        return {

            "message":
                "Document processed successfully",

            "document_id":
                document.id,

            "page_count":
                document.page_count,

            "chunk_count":
                document.chunk_count,

            "processing_status":
                document.processing_status,
        }

    except Exception as exc:

        db.rollback()

        document.processing_status = (
            "failed"
        )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Document processing failed: "
                + str(exc)
            ),
        )


# ============================================================
# INDEX DOCUMENT
# ADMIN + KNOWLEDGE MANAGER
# ============================================================

@router.post(
    "/{document_id}/index",
)
def index_uploaded_document(
    document_id: int,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        require_roles([
            "admin",
            "knowledge_manager",
        ])
    ),
):

    # --------------------------------------------------------
    # Find document
    # --------------------------------------------------------

    document = get_document_or_404(
        document_id=document_id,
        db=db,
    )

    # --------------------------------------------------------
    # Must be processed first
    # --------------------------------------------------------

    if (
        document.processing_status
        != "processed"
    ):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Document must be "
                "processed before indexing."
            ),
        )

    # --------------------------------------------------------
    # Set indexing state
    # --------------------------------------------------------

    document.indexing_status = (
        "indexing"
    )

    db.commit()

    # --------------------------------------------------------
    # Index
    # --------------------------------------------------------

    try:

        indexed_count = index_document(
            document=document,
            db=db,
        )

        document.indexing_status = (
            "indexed"
        )

        document.indexed_chunk_count = (
            indexed_count
        )

        db.commit()

        db.refresh(
            document
        )

        return {

            "message":
                "Document indexed successfully",

            "document_id":
                document.id,

            "indexed_chunks":
                indexed_count,

            "indexing_status":
                document.indexing_status,
        }

    except Exception as exc:

        db.rollback()

        document.indexing_status = (
            "failed"
        )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Document indexing failed: "
                + str(exc)
            ),
        )


# ============================================================
# APPROVE DOCUMENT
# ADMIN + KNOWLEDGE MANAGER
# ============================================================

@router.patch(
    "/{document_id}/approve",
    status_code=status.HTTP_200_OK,
)
def approve_document(
    document_id: int,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        require_roles([
            "admin",
            "knowledge_manager",
        ])
    ),
):

    # --------------------------------------------------------
    # Find document
    # --------------------------------------------------------

    document = get_document_or_404(
        document_id=document_id,
        db=db,
    )

    # --------------------------------------------------------
    # Processing required
    # --------------------------------------------------------

    if (
        document.processing_status
        != "processed"
    ):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Document must be processed "
                "before approval."
            ),
        )

    # --------------------------------------------------------
    # Indexing required
    # --------------------------------------------------------

    if (
        document.indexing_status
        != "indexed"
    ):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Document must be indexed "
                "before approval."
            ),
        )

    # --------------------------------------------------------
    # Already approved
    # --------------------------------------------------------

    if document.status == "approved":

        return {

            "message":
                "Document is already approved",

            "document_id":
                document.id,

            "status":
                document.status,
        }

    # --------------------------------------------------------
    # Approve
    # --------------------------------------------------------

    document.status = (
        "approved"
    )

    try:

        db.commit()

        db.refresh(
            document
        )

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to approve document.",
        )

    return {

        "message":
            "Document approved successfully",

        "document_id":
            document.id,

        "document_name":
            document.name,

        "version":
            document.version,

        "status":
            document.status,

        "approved_by":
            current_user.id,
    }


# ============================================================
# REJECT DOCUMENT
# ADMIN + KNOWLEDGE MANAGER
# ============================================================

@router.patch(
    "/{document_id}/reject",
    status_code=status.HTTP_200_OK,
)
def reject_document(
    document_id: int,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        require_roles([
            "admin",
            "knowledge_manager",
        ])
    ),
):

    # --------------------------------------------------------
    # Find document
    # --------------------------------------------------------

    document = get_document_or_404(
        document_id=document_id,
        db=db,
    )

    # --------------------------------------------------------
    # Already rejected
    # --------------------------------------------------------

    if document.status == "rejected":

        return {

            "message":
                "Document is already rejected",

            "document_id":
                document.id,

            "status":
                document.status,
        }

    # --------------------------------------------------------
    # Reject
    # --------------------------------------------------------

    document.status = (
        "rejected"
    )

    try:

        db.commit()

        db.refresh(
            document
        )

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to reject document.",
        )

    return {

        "message":
            "Document rejected successfully",

        "document_id":
            document.id,

        "document_name":
            document.name,

        "version":
            document.version,

        "status":
            document.status,

        "rejected_by":
            current_user.id,
    }