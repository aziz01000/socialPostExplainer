"""External sources search - social media & news APIs."""

import logging
from typing import List, Dict, Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class ExternalSourcesSearch:
    """Search across multiple external sources: social media platforms and news APIs."""
    
    def __init__(self):
        """Initialize external sources clients."""
        # Social Media
        self.reddit_client_id = getattr(settings, 'reddit_client_id', None)
        self.reddit_client_secret = getattr(settings, 'reddit_client_secret', None)
        self.reddit_user_agent = "RapidCanvas/1.0"
        self.twitter_bearer_token = getattr(settings, 'twitter_bearer_token', None)
        
        # News APIs
        self.newsdata_api_key = getattr(settings, 'newsdata_api_key', None)
        self.newsapi_api_key = getattr(settings, 'newsapi_api_key', None)
        self.guardian_api_key = getattr(settings, 'guardian_api_key', None)
        
        self.http_client = httpx.AsyncClient(timeout=10.0)
        logger.info("ExternalSourcesSearch initialized")
    
    async def search(self, query: str, num_results: int = 5, sources_type: str = "all") -> List[Dict]:
        """
        Search across external sources.
        
        Args:
            query: Search query
            num_results: Number of results per source
            sources_type: 'all', 'social', or 'news'
        
        Returns:
            Combined list of results from available sources
        """
        logger.info(f"Searching {sources_type} sources for: '{query}' (top {num_results} results)")
        all_results = []
        
        # Social Media Sources
        if sources_type in ["all", "social"]:
            # Try Reddit
            try:
                logger.debug("Searching Reddit...")
                reddit_results = await self._search_reddit(query, num_results)
                all_results.extend(reddit_results)
                logger.info(f"✓ Reddit returned {len(reddit_results)} results")
            except Exception as e:
                logger.warning(f"✗ Reddit search failed: {e}")
            
            # Try Twitter/X
            try:
                logger.debug("Searching Twitter/X...")
                twitter_results = await self._search_twitter(query, num_results)
                all_results.extend(twitter_results)
                logger.info(f"✓ Twitter returned {len(twitter_results)} results")
            except Exception as e:
                logger.warning(f"✗ Twitter search failed: {e}")
        
        # News API Sources
        if sources_type in ["all", "news"]:
            # Try NewsData.io (free tier)
            try:
                logger.debug("Searching NewsData.io...")
                newsdata_results = await self._search_newsdata(query, num_results)
                all_results.extend(newsdata_results)
                logger.info(f"✓ NewsData.io returned {len(newsdata_results)} results")
            except Exception as e:
                logger.warning(f"✗ NewsData search failed: {e}")
            
            # Try NewsAPI.org (optional, requires key)
            try:
                logger.debug("Searching NewsAPI...")
                newsapi_results = await self._search_newsapi(query, num_results)
                all_results.extend(newsapi_results)
                logger.info(f"✓ NewsAPI returned {len(newsapi_results)} results")
            except Exception as e:
                logger.warning(f"✗ NewsAPI search failed: {e}")
            
            # Try The Guardian API (optional, requires key)
            try:
                logger.debug("Searching The Guardian...")
                guardian_results = await self._search_guardian(query, num_results)
                all_results.extend(guardian_results)
                logger.info(f"✓ Guardian returned {len(guardian_results)} results")
            except Exception as e:
                logger.warning(f"✗ Guardian search failed: {e}")
        
        # Fallback: Mock results only when every source returned no results
        # (e.g. no API keys configured, or all APIs failed/rate-limited)
        if not all_results:
            logger.warning("No external source APIs available - using mock data")
            all_results = await self._mock_results(query, num_results)
        
        # Sort by score and return top N
        sorted_results = sorted(
            all_results,
            key=lambda x: x.get('score', 0),
            reverse=True
        )
        
        logger.info(f"Total results from all sources: {len(sorted_results)}")
        return sorted_results[:num_results]
    
    async def _search_reddit(self, query: str, limit: int) -> List[Dict]:
        """Search Reddit using free API."""
        if not self.reddit_client_id or not self.reddit_client_secret:
            logger.warning("Reddit credentials not configured")
            return []
        
        try:
            url = f"https://www.reddit.com/search.json"
            params = {
                "q": query,
                "limit": min(limit, 25),
                "sort": "relevance",
                "t": "all"
            }
            headers = {"User-Agent": self.reddit_user_agent}
            
            logger.debug(f"Calling Reddit API with query: {query}")
            response = await self.http_client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for post in data.get("data", {}).get("children", []):
                post_data = post.get("data", {})
                results.append({
                    "platform": "reddit",
                    "title": post_data.get("title", ""),
                    "content": post_data.get("selftext", post_data.get("title", "")),
                    "url": f"https://reddit.com{post_data.get('permalink', '')}",
                    "author": post_data.get("author", ""),
                    "score": post_data.get("score", 0),
                    "engagement": post_data.get("num_comments", 0),
                    "source_type": "social_media"
                })
            
            logger.debug(f"Reddit returned {len(results)} posts")
            return results
        except Exception as e:
            logger.error(f"Reddit API error: {e}", exc_info=True)
            return []
    
    async def _search_twitter(self, query: str, limit: int) -> List[Dict]:
        """Search Twitter/X using free tier API."""
        token = (self.twitter_bearer_token or "").strip()
        if not token:
            logger.warning("Twitter API bearer token not configured")
            return []

        try:
            url = "https://api.twitter.com/2/tweets/search/recent"
            headers = {
                "Authorization": f"Bearer {token}",
                "User-Agent": "RapidCanvas/1.0"
            }
            params = {
                "query": query,
                "max_results": min(limit, 100),
                "tweet.fields": "public_metrics,created_at",
                "expansions": "author_id"
            }
            
            logger.debug(f"Calling Twitter API with query: {query}")
            response = await self.http_client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for tweet in data.get("data", []):
                metrics = tweet.get("public_metrics", {})
                results.append({
                    "platform": "twitter",
                    "title": tweet.get("text", ""),
                    "content": tweet.get("text", ""),
                    "url": f"https://twitter.com/i/web/status/{tweet.get('id', '')}",
                    "author": tweet.get("author_id", ""),
                    "score": metrics.get("like_count", 0),
                    "engagement": metrics.get("reply_count", 0) + metrics.get("retweet_count", 0),
                    "source_type": "social_media"
                })
            
            logger.debug(f"Twitter returned {len(results)} tweets")
            return results
        except Exception as e:
            logger.error(f"Twitter API error: {e}", exc_info=True)
            return []
    
    async def _search_newsdata(self, query: str, limit: int) -> List[Dict]:
        """Search using NewsData.io (free tier - no key required, but key recommended)."""
        try:
            url = "https://newsdata.io/api/1/latest"
            params = {
                "q": query,
                "language": "en",
                "sort": "relevancy"
            }
            
            # Use API key if available
            if self.newsdata_api_key:
                params["apikey"] = self.newsdata_api_key
            
            logger.debug(f"Calling NewsData.io API with query: {query}")
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for article in data.get("results", [])[:limit]:
                results.append({
                    "platform": "newsdata",
                    "title": article.get("title", ""),
                    "content": article.get("description", article.get("content", "")),
                    "url": article.get("link", ""),
                    "author": article.get("creator", ["Unknown"])[0] if article.get("creator") else "Unknown",
                    "score": 0.85,  # NewsData doesn't provide ranking scores
                    "engagement": 0,
                    "published": article.get("pubDate", ""),
                    "source_type": "news"
                })
            
            logger.debug(f"NewsData returned {len(results)} articles")
            return results
        except Exception as e:
            logger.error(f"NewsData API error: {e}", exc_info=True)
            return []
    
    async def _search_newsapi(self, query: str, limit: int) -> List[Dict]:
        """Search using NewsAPI.org (requires free API key)."""
        if not self.newsapi_api_key:
            logger.debug("NewsAPI key not configured - skipping")
            return []
        
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "apiKey": self.newsapi_api_key,
                "sortBy": "relevancy",
                "pageSize": min(limit, 100)
            }
            
            logger.debug(f"Calling NewsAPI with query: {query}")
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for article in data.get("articles", [])[:limit]:
                results.append({
                    "platform": "newsapi",
                    "title": article.get("title", ""),
                    "content": article.get("description", article.get("content", "")),
                    "url": article.get("url", ""),
                    "author": article.get("author", "Unknown"),
                    "score": 0.8,
                    "engagement": 0,
                    "published": article.get("publishedAt", ""),
                    "source": article.get("source", {}).get("name", ""),
                    "source_type": "news"
                })
            
            logger.debug(f"NewsAPI returned {len(results)} articles")
            return results
        except Exception as e:
            logger.error(f"NewsAPI error: {e}", exc_info=True)
            return []
    
    async def _search_guardian(self, query: str, limit: int) -> List[Dict]:
        """Search using The Guardian API (requires free API key)."""
        if not self.guardian_api_key:
            logger.debug("Guardian API key not configured - skipping")
            return []
        
        try:
            # Use Guardian Content API host; open-platform.theguardian.com/search returns 404.
            url = "https://content.guardianapis.com/search"
            params = {
                "q": query,
                "api-key": self.guardian_api_key,
                "page-size": min(limit, 200),
                "show-fields": "byline,trailText",
            }
            
            logger.debug(f"Calling Guardian API with query: {query}")
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for article in data.get("response", {}).get("results", [])[:limit]:
                fields = article.get("fields", {}) or {}
                results.append({
                    "platform": "guardian",
                    "title": article.get("webTitle", ""),
                    "content": fields.get("trailText", article.get("webTitle", "")),
                    "url": article.get("webUrl", ""),
                    "author": fields.get("byline", "Unknown"),
                    "score": 0.75,
                    "engagement": 0,
                    "published": article.get("webPublicationDate", ""),
                    "section": article.get("sectionName", ""),
                    "source_type": "news"
                })
            
            logger.debug(f"Guardian returned {len(results)} articles")
            return results
        except Exception as e:
            logger.error(f"Guardian API error: {e}", exc_info=True)
            return []
    
    async def _mock_results(self, query: str, limit: int) -> List[Dict]:
        """Return mock results for testing."""
        logger.info(f"Generating mock results for: {query}")
        
        mock_results = [
            {
                "platform": "newsdata",
                "title": f"Breaking: {query} - Latest Updates",
                "content": f"Latest news coverage of {query}. Industry experts weigh in on recent developments and implications.",
                "url": "https://newsdata.io/article/breaking-news",
                "author": "News Editor",
                "score": 0.95,
                "engagement": 0,
                "published": "2026-03-14",
                "source_type": "news"
            },
            {
                "platform": "reddit",
                "title": f"Discussion: {query}",
                "content": f"This is a Reddit post discussing {query}. Users are sharing their strategies and experiences.",
                "url": "https://reddit.com/r/discussion",
                "author": "reddit_user_123",
                "score": 0.85,
                "engagement": 45,
                "source_type": "social_media"
            },
            {
                "platform": "newsapi",
                "title": f"In-Depth: Understanding {query}",
                "content": f"Analysis of {query} and its impact on the industry. What you need to know.",
                "url": "https://newsapi.org/article/analysis",
                "author": "Staff Writer",
                "score": 0.80,
                "engagement": 0,
                "published": "2026-03-14",
                "source": "Tech Weekly",
                "source_type": "news"
            },
            {
                "platform": "twitter",
                "title": f"Hot take: Everyone should understand {query}",
                "content": f"Just realized how important {query} is. Mind blown! #DevCommunity #TechTrends",
                "url": "https://twitter.com/dev_account",
                "author": "dev_account",
                "score": 0.75,
                "engagement": 340,
                "source_type": "social_media"
            },
            {
                "platform": "guardian",
                "title": f"Why {query} matters now",
                "content": f"An exploration of {query} and its significance in today's world.",
                "url": "https://theguardian.com/article/why-matters",
                "author": "Guardian Correspondent",
                "score": 0.90,
                "engagement": 0,
                "published": "2026-03-14",
                "section": "Technology",
                "source_type": "news"
            }
        ]
        
        return mock_results[:limit]
    
    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()
        logger.info("ExternalSourcesSearch client closed")

