import requests
import feedparser
import re

from ...config import (
        API_URL,
        DEFAULT_HEADERS
)

def fetch_arxiv_entries(
        query : str = "cat:cs.IA",
        max_results : int = 5,
        start : int = 0
) -> list[dict] :
        
        params = {
            "search_query": query,
            "start": start,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
    
        response = requests.get(
            API_URL,
            params=params,
            timeout=30,
            headers=DEFAULT_HEADERS
        )
    
        response.raise_for_status()
    
        feed = feedparser.parse(response.text)
    
        return list(feed.entries)

def extract_arxiv_id(entry: dict) -> str:

    raw_id = entry.get("id","")

    if not raw_id:
        raise ValueError("ID arXiv absent")

    arxiv_id = raw_id.split("/abs/")[-1]

    arxiv_id = re.sub(r"v\d+$", "", arxiv_id)

    return arxiv_id