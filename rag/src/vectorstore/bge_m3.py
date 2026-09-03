import chromadb
from pathlib import Path

from ..embeddings.bge_m3 import EmbeddingModel
from ...config import (
    CHROMA_DIR,
    COLLECTION_NAME
)

class ChromaVectorStore:

    def __init__(self, persist_directory: str = CHROMA_DIR, collection_name : str = COLLECTION_NAME) :
        self.client = chromadb.PersistentClient(
            path = persist_directory
        )

        self.collection = (
            self.client.get_or_create_collection(
                name = collection_name,
                configuration={
                    "hnsw":{
                        "space": "cosine"
                    }
                }
            )
        )

        self.embedding_model = EmbeddingModel()

        print(f"[CHROMA] Collection : {collection_name}")

    def add_chunks(self, chunks: list[dict], batch_size : int = 32):

        if not chunks:
            print("[CHROMA] Aucun chunk à ajouter")
            return

        texts = [
            chunk["text"]
            for chunk in chunks
        ]

        print(
            f"[EMBEDDING] Vectorisation de "
            f"{len(texts)} chunks..."
        )

        embeddings = self.embedding_model.encode(
            texts,
            batch_size = batch_size
        )

        ids = []

        metadatas = []

        documents = []

        for chunk in chunks:

            article_id = chunk["article_id"]

            chunk_id = chunk["chunk_id"]

            document_id = (
                f"{article_id}_{chunk_id}"
            )

            ids.append(
                document_id
            )

            documents.append(
                chunk["text"]
            )

            metadatas.append(
                {
                    "article_id": article_id,

                    "title": chunk.get(
                        "title",
                        ""
                    ),

                    "source": chunk.get(
                        "source",
                        ""
                    ),

                    "section": chunk.get(
                        "section"
                    ) or "",

                    "subsection": chunk.get(
                        "subsection"
                    ) or "",

                    "chunk_id": chunk_id,

                    "token_count": chunk.get(
                        "token_count",
                        0
                    ),
                }
            )

        self.collection.upsert(
            ids = ids,
            documents = documents,
            embeddings = embeddings,
            metadatas = metadatas
        )

        print(
                f"[CHROMA] "
                f"{len(chunks)} chunks enregistrés."
            )

    def count(self) -> int:

        return self.collection.count()