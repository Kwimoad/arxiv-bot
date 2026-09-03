from ..embeddings.bge_m3 import EmbeddingModel

class Retriever:

    def __init__(self, collection, embedding_model: EmbeddingModel):
        self.collection = collection
        self.embedding_model = embedding_model

    def retrieve(self, query: str, top_k: int = 5):

        query_embedding = self.embedding_model.encode(
            [query],
            batch_size = 1
        )[0]

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        retrieved_chunks = []

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances
        ):
            retrieved_chunks.append({
                "text": document,
                "metadata": metadata,
                "distance": distance
            })

        return retrieved_chunks