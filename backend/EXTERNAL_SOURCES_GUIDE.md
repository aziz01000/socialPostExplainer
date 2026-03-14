# Multi-Source External Search Guide

This guide explains how to use the social media & news API integration for the Q&A agent.

## Overview

The system now supports searching across **multiple free external sources** in addition to FAISS:

### Social Media Sources
- **Reddit** - Community discussions, user experiences
- **Twitter/X** - Real-time conversations, expert opinions

### News APIs  
- **NewsData.io** - Free news aggregation API (no auth required, but key optional)
- **NewsAPI.org** - Premium news API, requires free signup
- **The Guardian** - Open platform with quality journalism

## Configuration

### 1. Optional Setup (Default Mock Data)

If you don't configure any external APIs, the system will use mock data automatically.

### 2. Enable NewsData.io (Recommended)

You already have a free key in `.env`:
```
NEWSDATA_API_KEY=pub_3fc8da999693412488974f1c70d8aa0b
```

This works out of the box - no additional setup needed!

### 3. Enable Reddit (Optional)

Get credentials from: https://www.reddit.com/prefs/apps

```bash
# In .env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
```

### 4. Enable Twitter/X (Optional)

Get bearer token from: https://developer.twitter.com/en/portal/dashboard

```bash
# In .env
TWITTER_BEARER_TOKEN=your_bearer_token
```

### 5. Enable NewsAPI.org (Optional)

Sign up at: https://newsapi.org

```bash
# In .env
NEWSAPI_API_KEY=your_api_key
```

### 6. Enable The Guardian (Optional)

Sign up at: https://www.theguardian.com/open-platform

```bash
# In .env
GUARDIAN_API_KEY=your_api_key
```

## API Usage

### Endpoint: `POST /social-qa`

**Request:**
```json
{
  "question": "What is the Ralph Wiggum technique?",
  "sources_type": "all"
}
```

**Parameters:**
- `question` (string, required): The question to answer (3-1000 chars)
- `sources_type` (string, optional): Filter sources
  - `"all"` - Search all sources (default)
  - `"social"` - Only Reddit + Twitter
  - `"news"` - Only news APIs

### Response Structure

```json
{
  "question": "What is the Ralph Wiggum technique?",
  "answer": {
    "summary": "Comprehensive answer synthesizing all sources...",
    "source_count": 8,
    "generated": true
  },
  "sources": [
    {
      "title": "Source Title",
      "context": "Excerpt from the source",
      "relevance_score": 0.95,
      "url": "https://...",
      "platform": "newsdata",
      "engagement_score": 1250,
      "author": "Author Name"
    },
    ...
  ],
  "source_breakdown": {
    "faiss_docs": 3,
    "external_total": 5,
    "external_breakdown": {
      "social_media": 2,
      "news": 3
    },
    "combined_total": 8,
    "platforms": {
      "docs": 3,
      "newsdata": 2,
      "twitter": 1,
      "reddit": 1,
      "newsapi": 1
    }
  },
  "processing_time_ms": 2541
}
```

## Example Requests

### Get news only
```bash
curl -X POST http://localhost:8000/social-qa \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Latest developments in AI",
    "sources_type": "news"
  }'
```

### Get social media only
```bash
curl -X POST http://localhost:8000/social-qa \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Community perspectives on machine learning",
    "sources_type": "social"
  }'
```

### Get all sources (default)
```bash
curl -X POST http://localhost:8000/social-qa \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the Ralph Wiggum technique?"
  }'
```

## How It Works

### Step-by-step Process

1. **FAISS Search** - Query vector store for authoritative documents
2. **External Search** - Query configured APIs for real-time data
3. **Combine & Rank** - Merge and score all results by relevance
4. **LLM Synthesis** - Generate comprehensive answer citing sources
5. **Fallback** - If LLM unavailable, synthesize from sources directly

### Ranking Strategy

- FAISS documents get 1.2x boost (authoritative sources)
- News articles get 1.05x boost over social media  
- Engagement metrics boost social media relevance
- Top results from each source type combined

## Fallback Behavior

If any source/API fails:
- ✓ Gracefully continues with other sources
- ✓ Still returns high-quality answers
- ✓ Mock data used if all external APIs unavailable
- ✓ Full transparency in `source_breakdown`

## Testing

Run the test script:
```bash
python3 scripts/test_agents.py
```

Test specific source types:
```bash
# All sources
curl http://localhost:8000/social-qa -d '{"question":"test","sources_type":"all"}'

# News only
curl http://localhost:8000/social-qa -d '{"question":"test","sources_type":"news"}'

# Social media only
curl http://localhost:8000/social-qa -d '{"question":"test","sources_type":"social"}'
```

## Performance Tips

1. **Parallel requests**: System makes concurrent calls to all configured APIs
2. **Timeout handling**: 10-second timeout per API prevents blocking
3. **Engagement scoring**: Reddit upvotes/comments and Twitter likes automatically factor into ranking
4. **Source diversity**: System combines perspectives from academic, news, and community sources

## Cost Considerations

| Source | Cost | Setup |
|--------|------|-------|
| FAISS | Free | Included |
| Reddit | Free | OAuth required |
| Twitter | Free (academic, small scale) | Developer account |
| NewsData.io | Free | Already configured! |
| NewsAPI.org | Free (100 requests/day) | Free signup |
| The Guardian | Free | Free signup |

## Real-World Example

**Question:**  
"What are people saying about the latest AI regulations?"

**Results would include:**
- 📚 Authoritative documents from FAISS about AI policy
- 📰 News articles from multiple outlets about regulation changes
- 💬 Reddit discussions from AI communities
- 🐦 Twitter threads from industry experts

**Answer:** Synthesized perspective combining all viewpoints

## Troubleshooting

### No results returned
- Check `source_breakdown` to see which APIs returned data
- If all sources fail, mock data should appear
- Check `.env` for API key misconfigurations

### Slow responses
- First request may be slow (API timeouts)
- System caches results, subsequent requests faster
- Can set `sources_type` to limit API calls

### Missing sources
- Enable APIs in `.env`
- NewsData.io already enabled - no additional setup needed
- Other APIs optional, system continues without them

## Future Enhancements

Potential additions:
- YouTube comments/transcripts
- Hacker News discussions
- Academic papers via arXiv
- Product reviews from real users
- Job postings aggregation
