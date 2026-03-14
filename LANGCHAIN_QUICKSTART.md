# LangChain Agents - Quick Start Guide

## Installation

```bash
# Core LangChain packages
pip install langchain>=0.1.0 langchain-core>=0.1.0

# For OpenAI
pip install langchain-openai>=0.0.5

# For Google Gemini
pip install langchain-google-genai>=0.0.5
```

## Usage

### PostExplainerAgent (Explaining Posts)

**Same API as before - no changes needed:**

```python
from app.agents.post_explainer_agent import PostExplainerAgent

# Initialize
agent = PostExplainerAgent()
await agent.initialize()

# Use with text
result = await agent.explain_post(
    post_content="This is a social media post"
)

# Use with image
result = await agent.explain_post(
    post_content="Check out this photo",
    image_url="https://example.com/image.jpg"
)

# Result format
result = {
    "explanation": ["- Bullet point 1", "- Bullet point 2"],
    "sources": [...],
    "image_analysis": "...",
    "traces": {...}
}
```

### SocialMediaQAAgent (Question Answering)

**Same API as before - no changes needed:**

```python
from app.agents.social_media_qa_agent import SocialMediaQAAgent

# Initialize
qa_agent = SocialMediaQAAgent()
await qa_agent.initialize()

# Ask questions
result = await qa_agent.answer_question(
    question="What is machine learning?",
    sources_type="all"  # or "social", "news"
)

# Result format
result = {
    "question": "What is machine learning?",
    "answer": {
        "summary": "...",
        "source_count": 5,
        "generated": True
    },
    "sources": [...],
    "source_breakdown": {...}
}
```

## How It Works

### The ReAct Loop

```
┌─────────────────────────────────────┐
│ 1. Agent Thinks                     │
│    "What tools do I need?"          │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│ 2. Agent Acts                       │
│    Calls: retrieve_vector_store()   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│ 3. Agent Observes                   │
│    Gets tool results                │
└──────────────┬──────────────────────┘
               │
        Repeat 1-3 until...
        ├─ Final answer reached
        ├─ Max iterations (10)
        └─ Tool error occurs
               │
┌──────────────▼──────────────────────┐
│ 4. Final Answer                     │
│    Returns formatted response       │
└─────────────────────────────────────┘
```

## Available Tools

All agents have access to these tools:

### 1. `retrieve_vector_store(query, k=5)`
Search FAISS for authoritative documents
```python
# Agent automatically calls:
retrieve_vector_store("machine learning basics")
# Returns: "- Title1: content1 (Score: 0.95)\n- Title2: content2 (Score: 0.89)"
```

### 2. `retrieve_web_search(query, num_results=5)`
Search the web for information
```python
# Agent calls:
retrieve_web_search("latest AI research")
# Returns: formatted web search results
```

### 3. `search_external_sources(query, sources_type="all")`
Search social media + news
```python
# Agent calls:
search_external_sources("AI regulations", "news")
# Returns: formatted news articles + social posts
```

### 4. `analyze_image(image_url, question)`
Analyze an image using vision model
```python
# Agent calls:
analyze_image("https://...", "What's in this image?")
# Returns: image description or error message
```

### 5. `generate_explanation(post, sources, image_analysis=None)`
Generate explanation for a post
```python
# Agent calls:
generate_explanation("Post text", "Source contexts")
# Returns: bullet-point explanation
```

### 6. `generate_answer(question, sources)`
Generate answer to a question
```python
# Agent calls:
generate_answer("What is AI?", "Source contexts")
# Returns: comprehensive answer
```

### 7. `combine_sources(vector_sources, external_sources)`
Combine sources intelligently
```python
# Agent calls internally
# Returns: ranked and formatted combined sources
```

## Debugging

### Enable Verbose Output

```python
agent = PostExplainerAgent()
agent.agent_executor.verbose = True  # Shows all agent reasoning
await agent.explain_post("...")
```

### Check Logs

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("app.agents")

# Now you'll see all agent operations:
# Step 1: Running input guardrail
# Tool: Searching vector store for...
# Tool returned: ...
```

### Manual Tool Testing

```python
from app.agents.tools import retrieve_vector_store, retrieve_web_search

# Test a tool directly
results = await retrieve_vector_store("AI basics", k=3)
print(results)

# Test web search
web_results = await retrieve_web_search("machine learning", num_results=3)
print(web_results)
```

## Configuration

### Switch LLM Provider

In `.env`:

```bash
# Use OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# OR use Gemini
LLM_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3-flash-preview
```

### Adjust Agent Behavior

```python
# In agent._create_agent():
executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=self.tools,
    verbose=False,           # Show reasoning steps?
    max_iterations=10,       # Max tool calls per request
    handle_parsing_errors=True,  # Try to recover from errors
    early_stopping_method="force"
)
```

## Examples

### Example 1: Explain a Post

```python
agent = PostExplainerAgent()
await agent.initialize()

result = await agent.explain_post(
    post_content="Breaking: New AI model achieves 99% accuracy",
    image_url=None
)

print("Explanation:")
for bullet in result["explanation"]:
    print(bullet)
```

### Example 2: Answer with Multiple Sources

```python
qa_agent = SocialMediaQAAgent()
await qa_agent.initialize()

# Get news coverage
result = await qa_agent.answer_question(
    question="What are the latest developments in AI?",
    sources_type="news"
)

print("Answer:")
print(result["answer"]["summary"])

# Get social media discussion
result = await qa_agent.answer_question(
    question="What's the community's take on AI?",
    sources_type="social"
)

print("Community Perspectives:")
print(result["answer"]["summary"])
```

### Example 3: Debug Agent Reasoning

```python
agent = PostExplainerAgent()
agent.agent_executor.verbose = True  # Show all steps

result = await agent.explain_post(
    post_content="Check this out",
    image_url="https://..."
)

# You'll see output like:
# Thought: I need to analyze this image first
# Action: analyze_image
# Action Input: {"image_url": "https://...", "question": "..."}
# Observation: [Image contains...]
# Thought: Now I'll search for related information
# Action: retrieve_vector_store
# ...
```

## Common Issues & Solutions

### Issue: "Tool not found"
**Solution**: Tool name in agent prompt doesn't match tool registry. Check `tools.py`.

### Issue: Agent keeps calling same tool repeatedly
**Solution**: Normal - agent is gathering different results. Limit with `max_iterations=10`.

### Issue: Image analysis fails
**Solution**: 
- Ensure image URL is valid (starts with http://)
- Check that vision model is configured
- Check API key is set

### Issue: Slow responses
**Solution**:
- Reduce `max_iterations` in _create_agent()
- Use faster LLM model (gpt-4o-mini instead of gpt-4)
- Cache tool results if possible

## Production Deployment

### 1. Install Dependencies
```bash
pip install langchain langchain-core langchain-openai langchain-google-genai
```

### 2. Set Environment Variables
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
ENABLE_INPUT_MODERATION=true
ENABLE_OUTPUT_MODERATION=true
```

### 3. Monitor Performance
```python
import time

start = time.time()
result = await agent.explain_post(post_content)
duration = time.time() - start

print(f"Request completed in {duration:.2f}s")
```

### 4. Error Handling
```python
try:
    result = await agent.explain_post(post_content)
except ValueError as e:
    # Moderation blocked content
    return {"error": str(e), "status": 400}
except Exception as e:
    # Other errors
    logger.error(f"Agent error: {e}")
    return {"error": "Internal error", "status": 500}
```

## API Compatibility

The refactored agents are fully backward compatible with the API routes:

```python
# API route example (no changes needed)
@router.post("/explain")
async def explain_post(request: ExplainRequest):
    agent = req.app.state.agent
    result = await agent.explain_post(request.post_content)
    return ExplainResponse(explanation=result["explanation"])
```

## Next Steps

1. ✅ Install LangChain packages
2. ✅ Set environment variables
3. ✅ Start backend (agents initialize automatically)
4. ✅ Test endpoints (no API changes)
5. ✅ Monitor logs for agent reasoning
6. Consider: Add LangSmith tracing for production
7. Consider: Implement multi-turn conversation support
8. Consider: Add custom tools for specific domains

## Resources

- [LangChain Documentation](https://python.langchain.com/)
- [ReAct Paper](https://react-lm.github.io/)
- [LangChain Tools](https://python.langchain.com/docs/modules/tools/)
- [Agents Guide](https://python.langchain.com/docs/modules/agents/)
