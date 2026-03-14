"""Web search integration."""

from typing import List, Dict


class WebSearch:
    """Web search provider."""
    
    async def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """Search the web for relevant content.
        
        Returns list of results with 'title', 'url', 'snippet' fields.
        """
        # Placeholder - can integrate with SerpAPI, Bing, etc.
        return [
            {
                "title": "Result 1",
                "url": "https://example.com/1",
                "snippet": "Relevant content about the query."
            }
        ]
    
    async def close(self):
        """Cleanup."""
        pass
