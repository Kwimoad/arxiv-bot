from .pdf_extractor import clean_text
from .arxiv_api import extract_arxiv_id

def extract_metadata(
        entry: dict,
        page_count: int,
        pages: list[dict]
) -> dict:

    arxiv_id = extract_arxiv_id(entry)

    title = clean_text(
        entry.get("title", "")
    )

    abstract = clean_text(
        entry.get("summary", "")
    )

    authors = [
        author.get("name")
        for author in entry.get("authors", [])
        if author.get("name")
    ]

    published = entry.get("published", "")

    abs_url = entry.get("id", "")

    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    
    return {
        "arxiv_id": arxiv_id,

        "title": title or arxiv_id,
    
        "authors": authors,
    
        "abstract": abstract,
    
        "published": published,
    
        "url": abs_url,
    
        "pdf_url": pdf_url,
    
        "page_count": page_count,
    
        "pages": pages,
    
        "source": "arxiv",
    }