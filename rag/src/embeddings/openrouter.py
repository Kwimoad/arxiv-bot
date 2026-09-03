from langchain_core.embeddings import Embeddings
import requests
import time
from typing import List

from ...config import (
    OPENROUTER_MODEL,
    OPENROUTER_API_KEY,
    OPENROUTER_EMBEDDING_DIMENSIONS
)


class OpenRouterEmbeddings(Embeddings):

    def __init__(
        self,
        model: str = OPENROUTER_MODEL,
        api_key: str = OPENROUTER_API_KEY,
        batch_size: int = 100,
        max_retries: int = 5,
        dimensions: int = OPENROUTER_EMBEDDING_DIMENSIONS
    ):
        self.model = model
        self.api_key = api_key
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.dimensions = dimensions
        print(
            f"[EMBEDDING] OpenRouter prêt — modèle : {model}, "
            f"batch_size : {batch_size}, dimensions : {dimensions}"
        )

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "input": texts,
                        "encoding_format": "float",
                        "dimensions": self.dimensions,
                    },
                    timeout=30,
                )
                response.raise_for_status()
                return [item["embedding"] for item in response.json()["data"]]
            except requests.exceptions.RequestException as e:
                wait = 2 ** attempt
                print(f"[RETRY] Erreur API ({e}), nouvelle tentative dans {wait}s...")
                time.sleep(wait)
        raise RuntimeError(f"Echec après {self.max_retries} tentatives")

    def _embed(self, texts: List[str]) -> List[List[float]]:
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            all_embeddings.extend(self._embed_batch(batch))
        return all_embeddings

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embed(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._embed([text])[0]