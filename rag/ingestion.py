"""
============
Orchestrateur du pipeline d'ingestion.

Ce module coordonne l'ensemble du processus d'ingestion des articles
scientifiques. Il appelle successivement toutes les étapes nécessaires à la
construction de la base vectorielle :

    - lecture des fichiers Parquet ;
    - découpage en chunks ;
    - génération des embeddings ;
    - indexation dans la base vectorielle.
"""

from pathlib import Path

from .src.chunking.openrouter import chunk_article, read_all_parquet_files
from .src.vectorstore.openrouter import ChromaVectorStore

from .config import(
    PROCESSED_IDS_FILE
)

if PROCESSED_IDS_FILE.exists():
    processed_ids = set(PROCESSED_IDS_FILE.read_text().splitlines())
else:
    processed_ids = set()

print(
    f"[REPRISE] {len(processed_ids)} articles deja "
    f"indexes (checkpoint), ils seront ignores."
)

vector_store = ChromaVectorStore()
articles = read_all_parquet_files()

nb_article = 1

with open(PROCESSED_IDS_FILE, "a") as log_file:

    for metadata in articles:

        arxiv_id = metadata.get("arxiv_id")
        if arxiv_id in processed_ids:
            nb_article += 1
            continue

        chunks = chunk_article(metadata)

        print(
            f"[ARTICLE] N\u00b0{nb_article} \u2014 "
            f"{arxiv_id} \u2192 {len(chunks)} chunks"
        )

        try:
            vector_store.add_chunks(chunks)
        except Exception as e:
            print(
                f"[ERREUR] {arxiv_id} — {e}\n"
                f"Sera retenté au prochain lancement."
            )
            nb_article += 1
            del chunks
            continue

        log_file.write(arxiv_id + "\n")
        log_file.flush()
        processed_ids.add(arxiv_id)

        nb_article += 1
        del chunks