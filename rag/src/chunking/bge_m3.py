import re
from typing import List, Dict, Iterator
from pathlib import Path
from transformers import AutoTokenizer

import pyarrow.parquet as pq

from langchain_text_splitters import RecursiveCharacterTextSplitter

from ...config import (
    MODEL_NAME,
    EXCLUDED_SECTIONS,
    SECTION_NAMES,
    SECTION_PATTERN,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    PARQUET_DIR
)

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)

def normalize_text(text: str) -> str:

    text = re.sub(r"[ \t]+", " ", text)

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()

def normalize_section_name(name: str) -> str:

    name = name.lower().strip()

    name = re.sub(r"\s+", " ", name)

    return name

def read_parquet_file(
    parquet_file: Path
) -> Iterator[Dict]:

    table = pq.read_table(parquet_file)

    for metadata in table.to_pylist():
        yield metadata

def read_all_parquet_files(
    parquet_dir: Path = PARQUET_DIR
) -> Iterator[Dict]:

    parquet_files = sorted(
        parquet_dir.glob("batch_*.parquet")
    )

    for parquet_file in parquet_files:

        print(
            f"[PARQUET] Lecture : {parquet_file}"
        )

        yield from read_parquet_file(
            parquet_file
        )

def detect_sections(text: str) -> List[Dict]:

    lines = text.splitlines()

    sections = []

    current_section = None
    current_subsection = None
    current_text = []

    def save_current_section():

        if current_section is None:
            return

        content = "\n".join(current_text).strip()

        if not content:
            return

        sections.append(
            {
                "section": current_section,
                "subsection": current_subsection,
                "text": content,
            }
        )

    for line in lines:

        clean_line = line.strip()

        if not clean_line:
            current_text.append("")
            continue

        match = SECTION_PATTERN.match(clean_line)

        if match:

            save_current_section()

            section_name = normalize_section_name(
                match.group(1)
            )

            subsection_match = re.match(
                r"^\s*\d+(?:\.\d+)+\.?\s+",
                clean_line
            )

            if subsection_match:

                if current_section is not None:

                    current_subsection = section_name

                else:

                    current_section = section_name
                    current_subsection = None

            else:

                current_section = section_name
                current_subsection = None

            current_text = []

        else:

            current_text.append(line)

    save_current_section()

    return sections

def pages_to_text(pages: List[Dict]) -> str:

    page_texts = []

    for page in pages:

        text = page.get("text", "").strip()

        if text:
            page_texts.append(text)

    return "\n\n".join(page_texts)

def create_splitter() -> RecursiveCharacterTextSplitter :

    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE * 4,
                chunk_overlap=CHUNK_OVERLAP * 4,
        
                separators=[
                    "\n\n",
                    "\n",
                    ". ",
                    "? ",
                    "! ",
                    "; ",
                    ", ",
                    " ",
                    ""
                ],
        
                length_function=len,
        
                is_separator_regex=False,
    )

def approximate_token_count(text: str) -> int:

    tokens = tokenizer.encode(
        text,
        add_special_tokens=True
    )

    return len(tokens)


def chunk_article(
    metadata: Dict,
) -> List[Dict]:

    article_id = metadata["arxiv_id"]

    source = metadata.get(
        "url",
        ""
    )

    title = metadata.get(
        "title",
        ""
    )

    pages = metadata.get(
        "pages",
        []
    )

    text = pages_to_text(pages)

    text = normalize_text(text)

    if not text:

        return []

    sections = detect_sections(text)

    splitter = create_splitter()

    chunks = []

    chunk_id = 0

    if not sections:

        raw_chunks = splitter.split_text(text)

        for chunk in raw_chunks:

            chunk = chunk.strip()

            if not chunk:
                continue

            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "article_id": article_id,
                    "title": title,
                    "source": source,

                    "section": None,
                    "subsection": None,

                    "text": chunk,

                    "token_count":
                        approximate_token_count(chunk),
                }
            )

            chunk_id += 1

        return chunks


    for section_data in sections:

        section = section_data["section"]

        subsection = section_data["subsection"]

        content = section_data["text"].strip()

        if section in EXCLUDED_SECTIONS:
            continue

        if not content:
            continue


        raw_chunks = splitter.split_text(
            content
        )

        for chunk in raw_chunks:

            chunk = chunk.strip()

            if not chunk:
                continue

            chunks.append(
                {
                    "chunk_id": chunk_id,

                    "article_id": article_id,

                    "title": title,

                    "source": source,

                    "section": section,

                    "subsection": subsection,

                    "text": chunk,

                    "token_count":
                        approximate_token_count(chunk),
                }
            )

            chunk_id += 1

    return chunks