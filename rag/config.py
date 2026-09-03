from pathlib import Path
import re

API_URL = "https://export.arxiv.org/api/query"

DEFAULT_HEADERS = {"User-Agent": "arxiv-stream-ingest/1.0"}

OUTPUT_DIR = Path("data/metadata")

CHECKPOINT_FILE = OUTPUT_DIR / "checkpoint.json"

CATEGORIES = [
    "cs.AI",
    "cs.LG",
    "cs.CV",
    "cs.CL",
    "cs.IR",
    "cs.NE",
    "cs.RO",
    "cs.DS",
    "cs.DB",
    "cs.CR",
    "math.NA",
    "math.OC",
    "math.PR",
    "math.ST",
    "math.IT",
    "math.CO",
]

PARQUET_BATCH_SIZE = 1000

CHUNK_SIZE = 700
CHUNK_OVERLAP = 100

PARQUET_DIR = Path("data/metadata")

MODEL_NAME = "BAAI/bge-m3"

EXCLUDED_SECTIONS = {
    "references",
    "reference",
    "bibliography",
    "acknowledgements",
    "acknowledgments",
}

SECTION_NAMES = (
    r"abstract|"
    r"introduction|"
    r"background|"
    r"related\s+work|"
    r"literature\s+review|"
    r"method|"
    r"methods|"
    r"methodology|"
    r"materials?\s+and\s+methods|"
    r"approach|"
    r"model|"
    r"experiments?|"
    r"experimental\s+setup|"
    r"results?|"
    r"discussion|"
    r"analysis|"
    r"evaluation|"
    r"conclusion|"
    r"future\s+work|"
    r"limitations?|"
    r"references?|"
    r"bibliography|"
    r"acknowledgements?|"
    r"acknowledgments?"
)

SECTION_PATTERN = re.compile(
    rf"""
    ^
    \s*

    (?:
        # Numérotation classique
        # 1 Introduction
        # 1. Introduction
        # 3.2 Dataset
        \d+(?:\.\d+)*\.?\s+
        |

        # Numérotation romaine
        # I. INTRODUCTION
        # II. METHODS
        [IVXLCDM]+\.?\s+
        |

        # Lettre
        # A. MODEL
        [A-Z]\.?\s+
    )?

    ({SECTION_NAMES})

    \s*$
    """,
    re.IGNORECASE | re.VERBOSE
)

CHROMA_DIR = Path("data/chroma_db")

COLLECTION_NAME = "arxiv_articles"

OPENROUTER_MODEL = "text-embedding-3-small"

OPENROUTER_API_KEY = "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"

OPENROUTER_EMBEDDING_DIMENSIONS = 1024

PROCESSED_IDS_FILE = OUTPUT_DIR / "processed_ids.txt"

SYSTEM_PROMPT = """
        You are a scientific assistant specialized in research papers.

        Answer the user's question using only the provided context.

        Rules:
        - Do not invent information.
        - If the answer is not present in the context, say that you do not have enough information.
        - Give a clear and concise answer.
        - Use the information from the retrieved scientific papers.
    """