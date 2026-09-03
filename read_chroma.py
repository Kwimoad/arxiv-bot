import chromadb

# Charger ChromaDB
client = chromadb.PersistentClient(
    path="data/chroma"
)

# Récupérer la collection
collection = client.get_collection(
    name="arxiv_articles"
)

# Afficher le nombre de documents
print("Nombre de chunks :", collection.count())

# Lire les données
data = collection.get(
    limit=5,
    include=[
        "documents",
        "metadatas",
        "embeddings"
    ]
)

# Afficher
for i in range(len(data["ids"])):

    print("\n" + "=" * 80)

    print("ID :")
    print(data["ids"][i])

    print("\nTexte :")
    print(data["documents"][i])

    print("\nMetadata :")
    print(data["metadatas"][i])

    print("\nEmbedding :")
    print(data["embeddings"][i][:10])

    print("...")