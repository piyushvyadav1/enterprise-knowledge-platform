from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    id: int

    name: str
    original_filename: str

    department: str
    version: str
    status: str

    processing_status: str
    chunk_count: int

    access_level: str
    project_name: str | None
    search_weight: float
    owner_id: int | None

    indexing_status: str
    indexed_chunk_count: int

    file_size: int
    page_count: int | None

    uploaded_by: int
    uploaded_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )