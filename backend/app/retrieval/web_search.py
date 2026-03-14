"""Web search integration."""

from typing import List, Dict
import re
import httpx


class WebSearch:
    """Web search provider."""
    
    async def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """Search the web for relevant content.
        
        Returns list of results with 'title', 'url', 'snippet' fields.

        Implementation notes:
        - Uses Wikipedia search API as a keyless, stable source.
        - On network/API errors, falls back to a placeholder result so the system degrades gracefully.
        """
        q = (query or "").strip()
        if not q:
            return []

        # Wikipedia search endpoint
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": q,
            "format": "json",
            "utf8": 1,
            "srlimit": max(1, min(int(num_results), 10)),
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, params=params)
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
        except Exception:
            # Fallback: deterministic placeholder result.
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
