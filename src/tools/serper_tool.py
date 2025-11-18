import os
import requests
from typing import List, Dict

# NOTE: Serper API endpoint may be one of several; if 'https://api.serper.dev/search' doesn't work
# check your account docs at https://serper.dev. The code below uses api.serper.dev which is commonly used.
SERPER_SEARCH_URLS = [
    "https://api.serper.dev/search",
    "https://serper.dev/search",
    "https://google.serper.dev/search"
]

def search_serper(query: str, api_key: str = None, max_results: int = 5) -> List[Dict]:
    """Search Serper and return a list of simple result dicts: title, link, snippet, source."""
    if api_key is None:
        api_key = os.getenv('SERPER_API_KEY') or ''
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    payload = {'q': query, 'num': max_results}
    last_err = None
    for url in SERPER_SEARCH_URLS:
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                # Attempt to parse common fields; different endpoints may return slightly different shapes
                results = []
                # common top-level keys: 'organic', 'results', 'items'
                candidates = data.get('organic') or data.get('results') or data.get('items') or []
                for c in candidates[:max_results]:
                    title = c.get('title') or c.get('name') or c.get('link') or ''
                    link = c.get('link') or c.get('url') or c.get('displayLink') or None
                    snippet = c.get('snippet') or c.get('description') or c.get('snippetText') or ''
                    source = c.get('source') or c.get('displayLink') or None
                    results.append({'title': title, 'link': link, 'snippet': snippet, 'source': source})
                return results
            else:
                last_err = f"{url} returned {resp.status_code}: {resp.text[:200]}"
        except Exception as e:
            last_err = str(e)
    raise RuntimeError(f"Serper search failed. Last error: {last_err}") from None
