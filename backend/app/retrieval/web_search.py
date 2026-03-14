"""Web search integration."""

import logging
import re
from typing import Dict, List

import httpx

logger = logging.getLogger(__name__)

# Wikipedia requires a User-Agent; requests without one get 403.
WIKIPEDIA_USER_AGENT = (
    "ContextualPostExplainer/1.0 (https://github.com/contextual-post-explainer; bot) python-httpx/0.28"
)


class WebSearch:
    """Web search provider (Wikipedia API)."""

    async def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """Search the web for relevant content.

        Returns list of results with 'title', 'url', 'snippet' fields.
        Uses Wikipedia search API. On errors, returns a placeholder so the system degrades gracefully.
        """
        q = (query or "").strip()
        if not q:
            return []

        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": q,
            "format": "json",
            "utf8": 1,
            "srlimit": max(1, min(int(num_results), 10)),
        }
        headers = {"User-Agent": WIKIPEDIA_USER_AGENT}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            results = []
            for item in data.get("query", {}).get("search", [])[: params["srlimit"]]:
                title = item.get("title") or "Wikipedia"
                snippet_html = item.get("snippet") or ""
                snippet = re.sub(r"<[^>]+>", "", snippet_html)
                page_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                results.append(
                    {
                        "title": title,
                        "url": page_url,
                        "snippet": snippet,
                        "platform": "wikipedia",
                        "source_type": "web",
                    }
                )
            return results
        except Exception as e:
            logger.warning("Web search (Wikipedia) failed: %s", e, exc_info=True)
            return [
                {
                    "title": f"Web context for: {q[:40]}",
                    "url": None,
                    "snippet": f"(Web search unavailable) Try searching for: {q}",
                    "platform": "web",
                    "source_type": "web",
                }
            ]
    
    async def close(self):
        """Cleanup."""
        pass
