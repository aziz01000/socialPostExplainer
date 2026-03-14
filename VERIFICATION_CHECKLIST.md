# Quick Test & Verification Checklist

This checklist helps you verify that the multi-source Q&A system is working correctly.

## Pre-Flight Checks

- [ ] Python 3.11+ installed: `python3 --version`
- [ ] Backend dependencies installed: `pip install -r backend/requirements.txt`
- [ ] API keys in `.env`: 
  - [ ] OpenAI key (optional)
  - [ ] Gemini key (optional)
  - [ ] NewsData.io key (✅ already provided)

## Startup Verification

Run backend and verify startup output:

```bash
cd backend
python3 app/main.py
```

### Expected Startup Output

```
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO: Application startup complete

=== RapidCanvas Configuration Report ===
LLM Provider (for Q&A): gemini (using gemini-3-flash-preview)
Input Moderation: ✓ Enabled
Output Moderation: ✓ Enabled
Logging Level: INFO

OpenAI API: ✓ Configured
Gemini API: ✓ Configured

Social Media APIs (for Q&A):
  Reddit: ✗ Not configured (will use mock data)
  Twitter: ✗ Not configured (will use mock data)

News APIs (for Q&A):
  NewsData.io: ✓ Configured
  NewsAPI: ✗ Not configured (will use mock data)
  The Guardian: ✗ Not configured (will use mock data)

FAISS Vector Store: ✓ Loaded with 7 documents
```

✅ **Pass**: All checkmarks visible, system ready

## Basic Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

✅ **Pass**: Status is `healthy`

## Test 1: Basic Q&A Query

```bash
curl -X POST http://localhost:8000/social-qa \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the Ralph Wiggum technique?"}'
```

### Expected Response Structure

```json
{
  "question": "What is the Ralph Wiggum technique?",
  "answer": {
    "summary": "...", 
    "generated": true,
    "source_count": 3
  },
  "sources": [
    {
      "title": "...",
      "context": "...",
      "relevance_score": 0.9,
      "platform": "docs",
      "url": "..."
    }
  ],
  "source_breakdown": {
    "faiss_docs": 3,
    "external_total": 0,
    "combined_total": 3,
    "platforms": {"docs": 3}
  },
  "processing_time_ms": 1234
}
```

### Verification Checklist

- [ ] Response status 200
- [ ] `question` matches your query
- [ ] `answer.summary` is not empty
- [ ] `answer.generated` is `true`
- [ ] `sources` array has items
- [ ] `source_breakdown.faiss_docs` > 0 (at least using mock FAISS)
- [ ] `processing_time_ms` > 0

✅ **Pass**: All fields present and populated

## Test 2: All Sources Query

```bash
curl -X POST http://localhost:8000/social-qa \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the Ralph Wiggum technique?",
    "sources_type": "all"
  }'
```

### Expected Behavior

- Searches FAISS documents first
- Searches external sources in parallel:
  - NewsData.io ✓ (will work)
  - Reddit (mock fallback)
  - Twitter (mock fallback)
  - NewsAPI (mock fallback)
  - Guardian (mock fallback)
- Combines and ranks all results
- `source_breakdown.external_total` >= 0

### Verification

- [ ] `source_breakdown.faiss_docs` > 0
- [ ] `source_breakdown.external_total` >= 0
- [ ] `source_breakdown.combined_total` = faiss_docs + external_total
- [ ] Response includes docstrings + news articles + social posts

✅ **Pass**: Multiple source types in results

## Test 3: News-Only Query

```bash
curl -X POST http://localhost:8000/social-qa \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Latest AI developments",
    "sources_type": "news"
  }'
```

### Expected Behavior

- Does NOT search Reddit/Twitter (social media excluded)
- Searches FAISS (documents)
- Searches news APIs:
  - NewsData.io ✓ (enabled)
  - NewsAPI (mock fallback if no key)
  - Guardian (mock fallback if no key)
- Result should have news sources with publication dates

### Verification

- [ ] Response status 200
- [ ] `answer.summary` contains news-related content
- [ ] No social media platforms in `platforms` dict
- [ ] `source_breakdown.external_breakdown.news` > 0 OR external_breakdown has entries
- [ ] Sources have `published` dates (if from news APIs)

✅ **Pass**: Only news sources returned

## Test 4: Social-Media-Only Query

```bash
curl -X POST http://localhost:8000/social-qa \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Community experiences with AI agents",
    "sources_type": "social"
  }'
```

### Expected Behavior

- Does NOT search OpenAI/Gemini news APIs
- Searches FAISS (documents)
- Searches social media:
  - Reddit (mock fallback)
  - Twitter (mock fallback)
- Result should have community discussion tone

### Verification

- [ ] Response status 200
- [ ] `answer.summary` has community discussion language
- [ ] No news platforms in response
- [ ] `source_breakdown.external_breakdown.social_media` > 0 OR only has social entries
- [ ] Process was faster (fewer API calls than "all")

✅ **Pass**: Only social media sources returned

## Test 5: Invalid Source Type

```bash
curl -X POST http://localhost:8000/social-qa \
  -H "Content-Type: application/json" \
  -d '{
    "question": "test",
    "sources_type": "invalid"
  }'
```

### Expected Response

```
HTTP 400 Bad Request
{
  "detail": "sources_type must be 'all', 'social', or 'news'"
}
```

✅ **Pass**: Validation works

## Test 6: Explanation Endpoint

```bash
curl -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{
    "post_content": "Just learned about the Ralph Wiggum technique for AI agent iteration",
    "platform": "twitter",
    "engagement": 5000
  }'
```

### Expected Response Structure

```json
{
  "explanation": ["...", "...", "..."],
  "sources": [
    {
      "title": "...",
      "context": "...",
      "relevance_score": 0.85,
      "platform": "docs",
      "engagement_score": 150
    }
  ],
  "image_analysis": null,
  "processing_time_ms": 2345
}
```

### Verification

- [ ] Response status 200
- [ ] `explanation` is a list of strings (not empty)
- [ ] `sources` array has items
- [ ] `processing_time_ms` > 0
- [ ] Sources are from FAISS documents

✅ **Pass**: Explanation endpoint working

## Test 7: Run Full Test Suite

```bash
cd backend
python3 scripts/test_agents.py
```

### Expected Output

```
Testing Explain Endpoint...
... 
Testing Social-QA with ALL sources...
... 
Testing Social-QA with NEWS only...
... 
Testing Social-QA with SOCIAL MEDIA only...
... 

All tests completed!
```

### Verification

- [ ] Script runs without errors
- [ ] All three Q&A scenarios tested
- [ ] Shows source counts and breakdowns
- [ ] Shows answer summaries
- [ ] Shows engagement metrics

✅ **Pass**: Full test suite passes

## Performance Benchmarks

For reference, expected response times (local machine):

| Query Type | Time (seconds) | Notes |
|-----------|---|---|
| FAISS only | 0.5-1s | Vector search only |
| All sources | 3-6s | FAISS + 5 parallel API calls |
| News only | 2-3s | FAISS + 3 news APIs |
| Social only | 2-3s | FAISS + 2 social APIs |

Times may vary based on:
- Network latency to external APIs
- LLM response time (varies per provider)
- Mock data when real APIs unavailable (faster)

## Optional: Enable Real API Keys

### 1. NewsAPI.org (Optional - already have NewsData.io)

```bash
# Sign up at https://newsapi.org (free tier: 100 requests/day)
# Get your API key, then:
NEWSAPI_API_KEY=your_key_here
```

Then restart backend - will use real NewsAPI instead of mock data.

### 2. The Guardian (Optional)

```bash
# Sign up at https://www.theguardian.com/open-platform (free)
# Get your API key, then:
GUARDIAN_API_KEY=your_key_here
```

### 3. Twitter/X (Optional - requires academic account)

```bash
# Get Bearer token from https://developer.twitter.com/
TWITTER_BEARER_TOKEN=your_token_here
```

### 4. Reddit (Optional - requires OAuth)

```bash
# Create app at https://www.reddit.com/prefs/apps/
REDDIT_CLIENT_ID=your_id_here
REDDIT_CLIENT_SECRET=your_secret_here
```

After updating `.env`, restart backend to use real APIs.

## Debugging Tips

### View detailed logs

```bash
# In one terminal (backend):
cd backend
python3 app/main.py

# In another terminal (watch logs):
tail -f /tmp/rapidcanvas.log
```

### Check specific error

Look for logs with `✗` symbol:
```
✗ Twitter search failed: 401 Unauthorized
```

This means Twitter API failed but system continued with other sources (graceful degradation).

### Test with verbose curl

```bash
curl -vv -X POST http://localhost:8000/social-qa \
  -H "Content-Type: application/json" \
  -d '{"question":"test"}'
```

## Completion Checklist

Once all tests pass:

- [ ] Startup verification passed
- [ ] Health check passed  
- [ ] Test 1: Basic Q&A passed
- [ ] Test 2: All sources passed
- [ ] Test 3: News-only passed
- [ ] Test 4: Social-media-only passed
- [ ] Test 5: Invalid input validation passed
- [ ] Test 6: Explain endpoint passed
- [ ] Test 7: Full test suite passed
- [ ] Performance benchmarks noted

## Status

✅ **System is ready for use!**

You can now:
1. Query with combined sources (FAISS + news + social)
2. Filter by source type (all/news/social)
3. Explain social media posts with context
4. Get comprehensive source attribution
5. Deploy to production (see DEPLOYMENT.md)
6. Build React frontend (see frontend directory)
