import sys
from pathlib import Path

import chromadb

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from rag.src.embeddings.bge_m3 import EmbeddingModel
    from rag.src.retrievers.bge_m3 import Retriever
    from rag.src.rag.prompt import PromptBuilder
    from rag.src.rag.generator import Generator
    from rag.config import CHROMA_DIR, COLLECTION_NAME
else:
    from .embeddings.bge_m3 import EmbeddingModel
    from .retrievers.bge_m3 import Retriever
    from .rag.prompt import PromptBuilder
    from .rag.generator import Generator
    from ..config import CHROMA_DIR, COLLECTION_NAME


# ============================================================
# CONFIGURATION
# ============================================================

QUESTION = "What is IA?"

TOP_K = 5


# ============================================================
# CHROMADB
# ============================================================

client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = client.get_collection(
    name=COLLECTION_NAME
)


# ============================================================
# MODELES
# ============================================================

embedding_model = EmbeddingModel()

retriever = Retriever(
    collection=collection,
    embedding_model=embedding_model
)

prompt_builder = PromptBuilder()

generator = Generator()


# ============================================================
# RAG
# ============================================================

print("\nRecherche des documents...")

retrieved_chunks = retriever.retrieve(
    query=QUESTION,
    top_k=TOP_K
)

print(f"{len(retrieved_chunks)} chunks trouvés.")


prompt = prompt_builder.build(
    question=QUESTION,
    retrieved_chunks=retrieved_chunks
)


print("\nGénération de la réponse...")

answer = generator.generate(prompt)


# ============================================================
# RESULTAT
# ============================================================

print("\n" + "=" * 80)
print("QUESTION")
print("=" * 80)

print(QUESTION)

print("\n" + "=" * 80)
print("RÉPONSE")
print("=" * 80)

print(answer)

print("\n" + "=" * 80)