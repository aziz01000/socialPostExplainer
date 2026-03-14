#!/usr/bin/env python3
"""
Verify that when no external APIs are available (no keys or all fail),
ExternalSourcesSearch falls back to mock data.

Run from backend dir:
  python -m scripts.verify_mock_fallback

Or with no API keys to force mock (optional):
  REDDIT_CLIENT_ID= TWITTER_BEARER_TOKEN= NEWSAPI_API_KEY= NEWSDATA_API_KEY= GUARDIAN_API_KEY= python -m scripts.verify_mock_fallback
"""

import asyncio
import os
import sys

# Ensure backend app is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main():
    from app.retrieval.social_media_search import ExternalSourcesSearch

    search = ExternalSourcesSearch()
    query = "test query for mock verification"
    num_results = 5

    print("Query:", query)
    print("Checking external sources (Reddit, Twitter, NewsData, NewsAPI, Guardian)...")
    print("If no API keys are set or all APIs return empty, mock data is used.\n")

    results = await search.search(query, num_results=num_results, sources_type="all")
    await search.close()

    # Mock results have these platforms and query-dependent titles
    mock_platforms = {"newsdata", "reddit", "newsapi", "twitter", "guardian"}
    platforms_in_results = {r.get("platform") for r in results if r.get("platform")}

    print(f"Returned {len(results)} results.")
    print(f"Platforms: {sorted(platforms_in_results)}")

    # Heuristic: mock titles contain the query and template phrases
    sample_titles = [r.get("title", "") for r in results[:3]]
    looks_like_mock = (
        any("Breaking:" in t for t in sample_titles)
        or any("Discussion:" in t for t in sample_titles)
        or (platforms_in_results == mock_platforms and all(query.lower() in (r.get("title") or "").lower() or query.lower() in (r.get("content") or "").lower() for r in results))
    )

    if not results:
        print("\n❌ No results returned. APIs may have failed and mock fallback did not run (bug).")
        return 1
    if looks_like_mock or platforms_in_results == mock_platforms:
        print("\n✓ Mock fallback is in effect: results look like mock data (query in titles/content, all 5 platforms).")
        print("  This is expected when no external API keys are configured or all APIs return no results.")
    else:
        print("\n✓ Real API results returned (at least one provider had data).")
        print("  To force mock: unset all of REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, TWITTER_BEARER_TOKEN,")
        print("  NEWSAPI_API_KEY, NEWSDATA_API_KEY, GUARDIAN_API_KEY and run again.")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
