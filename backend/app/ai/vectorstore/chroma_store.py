from pathlib import Path

import chromadb


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[4]
)

CHROMA_DIR = (
    BASE_DIR / "chroma_data"
)


class ChromaVectorStore:

    def __init__(self):

        CHROMA_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.client = (
            chromadb.PersistentClient(
                path=str(CHROMA_DIR)
            )
        )

        self.collection = (
            self.client.get_or_create_collection(
                name="enterprise_knowledge",
                metadata={
                    "hnsw:space": "cosine"
                },
            )
        )


    def add_chunks(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:

        if not ids:
            return

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )


    def delete_document(
        self,
        document_id: int,
    ) -> None:

        self.collection.delete(
            where={
                "document_id":
                    document_id
            }
        )


    def search(
        self,
        query_embedding: list[float],
        limit: int = 5,
    ):

        return self.collection.query(
            query_embeddings=[
                query_embedding
            ],
            n_results=limit,
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )


_vector_store = None


def get_vector_store() -> ChromaVectorStore:

    global _vector_store

    if _vector_store is None:
        _vector_store = (
            ChromaVectorStore()
        )

    return _vector_store