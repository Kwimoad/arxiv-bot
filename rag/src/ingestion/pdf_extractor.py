import requests
import re
import fitz

from ...config import DEFAULT_HEADERS

def download_pdf_bytes(arxiv_id: str) -> bytes:

    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    response = requests.get(
        pdf_url,
        timeout = 60,
        headers = DEFAULT_HEADERS
    )

    response.raise_for_status()

    pdf_bytes = response.content

    if not pdf_bytes.startswith(b"%PDF"):
        raise ValueError(
            f"La réponse pour {arxiv_id} n'est pas un PDF valide."
        )

    return pdf_bytes

def clean_text(text: str) -> str:
    
    text = re.sub(r"[ \t]+", " ", text)

    text = re.sub(r" *\n *", "\n", text)

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()

def is_page_number(text :str) -> bool:

    text = text.strip()

    patterns = [
        r"^\d+$",
        r"^-\s*\d+\s*-$",
        r"^page\s+\d+$",
        r"^\d+\s*/\s*\d+$",
    ]

    return any(
        re.match(
            pattern,
            text,
            re.IGNORECASE
        )
        for pattern in patterns
    )

def extract_pdf_text(
    pdf_bytes: bytes
) -> tuple[list[dict], int]:

    pages = []

    with fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    ) as doc:

        page_count = len(doc)

        repeated_blocks = {}

        for page in doc:

            page_height = page.rect.height

            blocks = page.get_text("blocks")

            for block in blocks:

                x0, y0, x1, y1, text = block[:5]

                text = clean_text(text)

                if not text:
                    continue

                is_header = (
                    y0 < page_height * 0.10
                )

                is_footer = (
                    y1 > page_height * 0.90
                )

                if is_header or is_footer:

                    key = text.lower()

                    repeated_blocks[key] = (
                        repeated_blocks.get(
                            key,
                            0
                        ) + 1
                    )

        for page_number, page in enumerate(
            doc,
            start=1
        ):

            page_height = page.rect.height

            blocks = page.get_text("blocks")

            page_text = []

            for block in blocks:

                x0, y0, x1, y1, text = block[:5]

                text = clean_text(text)

                if not text:
                    continue

                if is_page_number(text):
                    continue

                is_header = (
                    y0 < page_height * 0.10
                )

                is_footer = (
                    y1 > page_height * 0.90
                )

                if (
                    (is_header or is_footer)
                    and repeated_blocks.get(
                        text.lower(),
                        0
                    ) >= 2
                ):
                    continue

                page_text.append(text)

            text = clean_text(
                "\n\n".join(page_text)
            )

            if text:

                pages.append(
                    {
                        "page": page_number,
                        "text": text
                    }
                )

    return pages, page_count