from ..embeddings.openrouter import OpenRouterEmbeddings

class Retriever:

    def __init__(self, collection, embedding_model: OpenRouterEmbeddings):
        self.collection = collection
        self.embedding_model = embedding_model

    def retrieve(self, query: str, top_k: int = 5):

        query_embedding = self.embedding_model.embed_query(query)

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