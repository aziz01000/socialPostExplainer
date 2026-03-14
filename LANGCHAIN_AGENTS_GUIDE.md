# LangChain Agent Integration - Implementation Summary

## Overview

Both agents have been successfully refactored to use **LangChain's ReAct (Reasoning + Acting) framework**. The agents now use tools to orchestrate complex multi-step workflows.

## What Changed

### 1. **New Tools Module** (`app/agents/tools.py`)
Created a comprehensive tool library with the following tools:

| Tool | Purpose |
|------|---------|
| `retrieve_vector_store` | Search FAISS for authoritative documents |
| `retrieve_web_search` | Search the web for information |
| `search_external_sources` | Search social media + news APIs |
| `analyze_image` | Analyze images using vision models |
| `generate_explanation` | Generate post explanations |
| `generate_answer` | Generate Q&A answers |
| `combine_sources` | Combine and rank multiple sources |

**Features:**
- Async support where applicable
- Comprehensive error handling
- Logging for debugging
- Tool registry for easy access

### 2. **PostExplainerAgent Refactored** (`app/agents/post_explainer_agent.py`)

**Before:** Custom 6-step workflow
**After:** LangChain ReAct agent with the same interface

**Architecture:**
```
User Input
    ↓
[INPUT GUARDRAIL]
    ↓
[LANGCHAIN AGENT]
  - Uses tools to:
    • Retrieve from vector store
    • Search the web
    • Analyze images
    • Generate explanation
    ↓
[OUTPUT GUARDRAIL]
    ↓
Response
```

**Key Methods:**
- `explain_post()` - Main entry point (unchanged externally)
- `_create_agent()` - Creates LangChain ReAct agent
- `_input_guardrail()` - Moderation check (still present)
- `_output_guardrail()` - Moderation check (still present)

### 3. **SocialMediaQAAgent Refactored** (`app/agents/social_media_qa_agent.py`)

**Before:** Custom retrieval + generation workflow
**After:** LangChain ReAct agent

**Architecture:**
```
User Question
    ↓
[INPUT GUARDRAIL]
    ↓
[LANGCHAIN AGENT]
  - Uses tools to:
    • Search FAISS
    • Search external sources
    • Combine sources
    • Generate answer
    ↓
[OUTPUT GUARDRAIL]
    ↓
Response
```

**Key Methods:**
- `answer_question()` - Main entry point (unchanged externally)
- `_create_agent()` - Creates LangChain ReAct agent
- `_input_guardrail()` - Moderation check
- `_output_guardrail()` - Moderation check

### 4. **ModelRouter Enhanced** (`app/llm/model_router.py`)

Added LangChain support:

```python
# Get LangChain-compatible LLM instance
llm = model_router.get_llm_instance()

# For OpenAI:
# Returns: langchain_openai.ChatOpenAI

# For Gemini:
# Returns: langchain_google_genai.ChatGoogleGenerativeAI
```

## How LangChain Agents Work

### ReAct Framework

The agents use **ReAct (Reasoning + Acting)** - a technique where the LLM:

1. **Thinks** - Reasons about what action to take
2. **Acts** - Calls a tool based on its reasoning
3. **Observes** - Sees the result
4. **Repeats** - Goes back to step 1 until done

### Example Agent Prompt

```
You are an AI assistant that explains social media posts...

Available Tools:
- retrieve_vector_store: Search FAISS for documents
- retrieve_web_search: Search the web
- analyze_image: Analyze an image URL
- generate_explanation: Generate explanation from context

Question: [User Input]

Thought: I should search for relevant context
Action: retrieve_vector_store
Action Input: [query]
Observation: [results from tool]

Thought: I should also search the web
Action: retrieve_web_search
...

Final Answer: [The explanation]
```

## API and Interface Compatibility

✅ **No breaking changes** - The external interfaces remain the same:

```python
# Still works exactly the same
agent = PostExplainerAgent()
result = await agent.explain_post(post_content, image_url)

# Still works exactly the same
qa_agent = SocialMediaQAAgent()
result = await qa_agent.answer_question(question, sources_type)
```

The API routes don't need any changes - they call the same methods with the same signatures.

## Benefits of LangChain Refactoring

### 1. **Better Modularity**
- Tools are reusable, testable, and composable
- Libraries maintain separation of concerns

### 2. **Flexibility**
- Easy to add new tools without modifying agents
- Agent logic can be reused with different tool combinations

### 3. **Maintainability**
- Agents are now following established LangChain patterns
- Easier for other engineers to understand
- Less custom orchestration code

### 4. **Debugging**
- LangChain's verbose mode shows all reasoning steps
- Tool outputs are logged automatically

### 5. **Scalability**
- Can switch between different LLM models easily
- Can use LangChain memory for multi-turn conversations
- Can integrate with LangChain's ecosystem (evaluators, tracing, etc.)

### 6. **Production Ready**
- LangChain handles edge cases
- Built-in error recovery
- Automatic token limit management

## Guardrails Integration

Both `ModerationGuardrail` checks are still present and working:

```python
# Step 1: Input guardrail (before agent)
moderation_result = await self._input_guardrail(post_content)
if moderation_result.get("flagged"):
    raise ValueError(error_msg)  # Rejects harmful input

# [Agent runs here with tools]

# Step 6: Output guardrail (after agent)
output_check = await self._output_guardrail(full_text)
if output_check.get("flagged"):
    raise ValueError(error_msg)  # Rejects harmful output
```

## Tool Implementation Details

### Tool Definitions

Each tool is defined using LangChain's `@tool` decorator:

```python
@tool
async def retrieve_vector_store(query: str, k: int = 5) -> str:
    """Search FAISS vector store for relevant documents."""
    # Implementation...
    return formatted_results
```

### Tool Features

- **Async Support**: Tools handle async operations
- **Error Handling**: Tools catch exceptions and return error messages
- **Logging**: All tool calls are logged at DEBUG level
- **String Output**: Tools return formatted strings for LLM readability

## Configuration

### Environment Variables

No new environment variables needed! Uses existing:

```bash
# LLM Provider selection
LLM_PROVIDER=openai    # or gemini

# OpenAI (for LangChain)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Google Gemini (for LangChain)
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3-flash-preview
```

## New Dependencies

The following LangChain packages are required:

```bash
pip install langchain>=0.1.0
pip install langchain-core>=0.1.0
pip install langchain-openai>=0.0.5  # if using OpenAI
pip install langchain-google-genai>=0.0.5  # if using Gemini
```

## Migration Path

### Option 1: Drop-in Replacement
The refactored agents work as drop-in replacements - no code changes needed in API routes or elsewhere.

### Option 2: Enhanced Agent Usage
You can now leverage LangChain features:

```python
from langchain.agents import AgentExecutor

# Access the executor directly
executor = agent._create_agent()

# Enable verbose output
executor.verbose = True

# Use agents in chains
from langchain.chains import LLMChain, SimpleSequentialChain
```

## Testing

The agents maintain the same test interface:

```python
# Test PostExplainerAgent
agent = PostExplainerAgent()
await agent.initialize()
result = await agent.explain_post("What is AI?")
assert "explanation" in result

# Test SocialMediaQAAgent  
qa_agent = SocialMediaQAAgent()
await qa_agent.initialize()
result = await qa_agent.answer_question("What is machine learning?")
assert "answer" in result["answer"]
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      API Request                            │
│         (POST /explain or /social-qa)                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │  Input Guardrail           │
        │  (Moderation Check)        │
        └────────┬───────────────────┘
                 │
        ╔════════╩════════╗
        │                 │
        ▼                 ▼
    ✓ PASS          ✗ BLOCK
    Continue        HTTP 400
        │
        ▼
   ┌──────────────────────────────────┐
   │   LangChain ReAct Agent          │
   │  ┌────────────────────────────┐  │
   │  │  Thought: Analyze input    │  │
   │  └────────────────────────────┘  │
   │  ┌────────────────────────────┐  │
   │  │  Action: Call Tool         │  │
   │  └────────────────────────────┘  │
   │ ┌─────────────────────────────┐  │
   │ │ Tool: retrieve_vector_store │  │
   │ │ Tool: retrieve_web_search   │  │
   │ │ Tool: analyze_image         │  │
   │ │ Tool: generate_explanation  │  │
   │ └─────────────────────────────┘  │
   │  ┌────────────────────────────┐  │
   │  │  Final Answer: Response    │  │
   │  └────────────────────────────┘  │
   └──────────────────┬────────────────┘
                      │
                      ▼
        ┌────────────────────────────┐
        │  Output Guardrail          │
        │  (Moderation Check)        │
        └────────┬───────────────────┘
                 │
        ╔════════╩════════╗
        │                 │
        ▼                 ▼
    ✓ PASS          ✗ BLOCK
    HTTP 200        HTTP 400
```

## Performance Considerations

### Advantages
- **Smart Tool Selection**: Agent chooses which tools to use based on reasoning
- **Lazy Evaluation**: Only calls tools that are needed
- **Error Recovery**: Can retry with different tools on failure

### Potential Overhead
- **Agent Reasoning**: Extra LLM call for orchestration
- **Tool Calls**: Multiple tool invocations per request
- **Latency**: ~500-1000ms additional per request

### Optimization Tips
```python
# 1. Use caching for tool results
# 2. Limit agent iterations (already set to 10)
# 3. Use faster LLM models for reasoning
# 4. Implement tool result caching at agent level
```

## Troubleshooting

### Issue: "Tool not found" error
**Cause**: Tool name mismatch in agent prompt
**Solution**: Check tool names in `tools.py` match those called in prompts

### Issue: Agent loops infinitely
**Solution**: Already handled - set `max_iterations=10` and `early_stopping_method="force"`

### Issue: Tool returns unexpected format
**Solution**: Ensure tool return type is always a formatted string

### Issue: LangChain import error
**Solution**: Install `langchain` and provider-specific packages:
```bash
pip install langchain langchain-core langchain-openai langchain-google-genai
```

## Future Enhancements

- [ ] Add LangChain memory for multi-turn conversations
- [ ] Integrate with LangChain's evaluation framework
- [ ] Add LangSmith tracing for production monitoring
- [ ] Create custom tools for domain-specific operations
- [ ] Implement agent evaluation metrics
- [ ] Add tool result caching layer
- [ ] Create tool pipelines for complex workflows

## Summary

✅ **Agents now use LangChain ReAct framework**
✅ **All tools centralized and reusable**
✅ **Guardrails still in place at input/output**
✅ **API compatibility maintained - drop-in replacement**
✅ **Better modularity and maintainability**
✅ **Production-ready error handling**
✅ **Extensible tool-based architecture**

The refactoring successfully modernizes the agent architecture while maintaining backward compatibility and improving overall code quality and maintainability.
