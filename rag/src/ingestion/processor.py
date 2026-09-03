import re
import pyarrow.parquet as pq

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import threading

from .checkpoint import load_checkpoint, save_checkpoint
from .storage import save_metadata_batch
from .metadata import extract_metadata
from .arxiv_api import fetch_arxiv_entries, extract_arxiv_id
from .pdf_extractor import download_pdf_bytes, extract_pdf_text

from ...config import (
    OUTPUT_DIR,
    CATEGORIES
)

processed_ids_lock = threading.Lock()

def load_processed_ids() -> set[str]:

    if not OUTPUT_DIR.exists():
        return set()

    parquet_files = list(OUTPUT_DIR.glob("batch_*.parquet"))

    if not parquet_files:
        return set()

    ids = set()

    for f in parquet_files:
        try:
            table = pq.read_table(f, columns=["arxiv_id"])
            ids.update(table["arxiv_id"].to_pylist())
        except Exception:
            continue

    return ids

def article_already_processed(
    arxiv_id: str
) -> bool:

    if not OUTPUT_DIR.exists():
        return False

    parquet_files = list(
        OUTPUT_DIR.glob("batch_*.parquet")
    )

    if not parquet_files:
        return False

    for parquet_file in parquet_files:

        try:

            table = pq.read_table(
                parquet_file,
                columns=["arxiv_id"]
            )

            arxiv_ids = (
                table["arxiv_id"].to_pylist()
            )

            if arxiv_id in arxiv_ids:
                return True

        except Exception:
            continue

    return False

def process_article(entry: dict, processed_ids: set[str]) -> dict | None:

    arxiv_id = extract_arxiv_id(entry)

    with processed_ids_lock:

        if arxiv_id in processed_ids:

            print(f"[SKIP] {arxiv_id} déjà traité")
            return None
        
        processed_ids.add(arxiv_id)

    pdf_bytes = download_pdf_bytes(arxiv_id)

    try:

        pages, page_count = extract_pdf_text(pdf_bytes)
        return extract_metadata(entry=entry, page_count=page_count, pages=pages)
    
    except Exception:

        with processed_ids_lock:

            processed_ids.discard(arxiv_id)
        raise

    finally:

        del pdf_bytes

"""""""""""
def process_article(entry: dict) -> dict | None:

    arxiv_id = extract_arxiv_id(entry)

    if article_already_processed(arxiv_id):

        print(
            f"[SKIP] {arxiv_id} déjà traité"
        )

        return None

    pdf_bytes = download_pdf_bytes(arxiv_id)

    try:

        pages, page_count = extract_pdf_text(pdf_bytes)

        metadata = extract_metadata(
            entry=entry,
            page_count=page_count,
            pages=pages
        )

        return metadata

    finally:

        del pdf_bytes
"""""""""

def process_articles(
    max_results: int = 1000,
    max_workers: int = 8
):

    checkpoint = load_checkpoint()
    processed_ids = load_processed_ids()

    existing_batches = list(
        OUTPUT_DIR.glob("batch_*.parquet")
    )

    if existing_batches:

        batch_numbers = []

        for file in existing_batches:

            match = re.search(
                r"batch_(\d+)\.parquet",
                file.name
            )

            if match:

                batch_numbers.append(
                    int(match.group(1))
                )

        if batch_numbers:

            batch_number = max(
                batch_numbers
            ) + 1

        else:

            batch_number = 0

    else:

        batch_number = 0

    for category in CATEGORIES:

        start = checkpoint[
            "categories"
        ][category]

        query = f"cat:{category}"

        print()
        print("=" * 60)
        print(f"[CATEGORY] {category}")
        print(f"[START] {start}")
        print(f"[MAX ARTICLES] {max_results}")
        print(f"[THREADS] {max_workers}")
        print("=" * 60)

        entries = fetch_arxiv_entries(
            query=query,
            max_results=max_results,
            start=start
        )

        if not entries:

            print(
                f"[DONE] {category} terminé."
            )

            continue

        success = 0
        failed = 0
        skipped = 0

        metadata_batch = []

        with ThreadPoolExecutor(
            max_workers=max_workers
        ) as executor:

            future_to_index = {}

            for index, entry in enumerate(entries):

                future = executor.submit(
                    process_article,
                    entry,
                    processed_ids
                )

                future_to_index[
                    future
                ] = index

            for future in as_completed(
                future_to_index
            ):

                index = future_to_index[
                    future
                ]

                current_position = (
                    start + index
                )

                entry = entries[
                    index
                ]


                try:

                    metadata = future.result()

                    if metadata is None:

                        skipped += 1

                    else:

                        metadata_batch.append(
                            metadata
                        )

                        success += 1

                        arxiv_id = (
                            extract_arxiv_id(
                                entry
                            )
                        )

                        print(
                            f"[OK] {arxiv_id}"
                        )

                    checkpoint[
                        "categories"
                    ][category] = max(
                        checkpoint[
                            "categories"
                        ][category],
                        current_position + 1
                    )

                    save_checkpoint(
                        checkpoint
                    )


                except Exception as e:

                    failed += 1

                    try:

                        arxiv_id = (
                            extract_arxiv_id(
                                entry
                            )
                        )

                    except Exception:

                        arxiv_id = "unknown"


                    print(
                        f"[ERROR] "
                        f"{category} / "
                        f"{arxiv_id} : "
                        f"{e}"
                    )

                    checkpoint[
                        "categories"
                    ][category] = max(
                        checkpoint[
                            "categories"
                        ][category],
                        current_position + 1
                    )

                    save_checkpoint(
                        checkpoint
                    )

        if metadata_batch:

            print()
            print(
                "[SAVE] Tous les articles ont été traités."
            )

            print(
                f"[SAVE] "
                f"Sauvegarde de "
                f"{len(metadata_batch)} articles..."
            )


            output_file = save_metadata_batch(
                metadata_batch,
                batch_number
            )


            print(
                f"[PARQUET] {output_file}"
            )


            batch_number += 1

        else:

            print(
                "[SAVE] Aucun nouvel article à sauvegarder."
            )

        save_checkpoint(
            checkpoint
        )

        print()
        print("=" * 60)
        print(
            f"[RESULT] {category}"
        )

        print(
            f"  Succès       : {success}"
        )

        print(
            f"  Échecs       : {failed}"
        )

        print(
            f"  Déjà traités : {skipped}"
        )

        print(
            f"  Sauvegardés  : "
            f"{len(metadata_batch)}"
        )

        print(
            f"  Prochain start : "
            f"{checkpoint['categories'][category]}"
        )

        print("=" * 60)

if __name__ == "__main__":

    process_articles(
        max_results=1000,
        max_workers=8
    )