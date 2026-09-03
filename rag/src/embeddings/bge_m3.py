from sentence_transformers import SentenceTransformer

from ...config import MODEL_NAME

class EmbeddingModel:

    def __init__(self, model_name: str = MODEL_NAME):
        self.model = SentenceTransformer(model_name)
        print("EMBEDDING] Modèle chargé")

    def encode(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        if not texts:
            return []

        embedding = self.model.encode(
            texts,
            batch_size = batch_size,
            show_progress_bar=True,
            normalize_embeddings=True
        )
        return embedding.tolist()