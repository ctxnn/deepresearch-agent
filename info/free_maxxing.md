# 💸 Free Maxxing — Running Deep Research for $0

> How and why we replaced every paid model with free alternatives to make the entire deep research multi-agent system run at zero cost.

---

## The Problem

Earlier we used **3 paid models** that cost real money per API call:

| Model | Cost | Used For |
|---|---|---|
| `anthropic:claude-sonnet-4-20250514` | ~$3/$15 per 1M tokens | Research agent brain, Supervisor decisions |
| `openai:gpt-4.1` | ~$2/$8 per 1M tokens | Brief generation, compression, final report |
| `openai:gpt-4.1-mini` | ~$0.40/$1.60 per 1M tokens | Webpage summarization |

A single deep research run could cost **$0.50–$2.00+** depending on the complexity of the query and number of parallel agents.

---

## What's Available for Free (June 2026)

### Groq Free Tier

Groq runs models on their custom **LPU (Language Processing Unit)** hardware — extremely fast inference, and they offer a generous free tier.

| Model ID | Params | Strengths | Tool Calling | Structured Output | Free Tier Limits |
|---|---|---|---|---|---|
| `llama-3.3-70b-versatile` | 70B | Best all-rounder. Excellent reasoning, coding, tool use | ✅ Native | ✅ `json_schema` + `function_calling` | ~30 RPM, ~300k TPM |
| `llama-3.1-8b-instant` | 8B | Ultra-fast, lightweight | ✅ Basic | ✅ Basic | ~30 RPM, ~250k TPM |
| `qwen/qwen3-32b` | 32B | Strong reasoning + coding | ✅ Native | ✅ Native | ~30 RPM |
| `openai/gpt-oss-120b` | 120B | Large, agentic tasks | ✅ Native | ✅ Native | ~30 RPM |
| `moonshotai/kimi-k2-instruct` | 1T MoE | Cutting-edge agentic intelligence | ✅ Native | ✅ Native | ~30 RPM |

**Key facts:**
- No credit card required
- Same LPU speed as paid users
- OpenAI-compatible API
- `langchain-groq` package has battle-tested `bind_tools()` and `with_structured_output()` support

### OpenRouter Free Tier

OpenRouter aggregates models from many providers. Free models have `:free` suffix.

| Model ID | Provider | Strengths | Tool Calling |
|---|---|---|---|
| `meta-llama/llama-3.3-70b-instruct:free` | Meta | General purpose | ✅ |
| `qwen/qwen3-coder:free` | Qwen | Coding, 1M context | ✅ |
| `deepseek/deepseek-r1:free` | DeepSeek | Reasoning | ✅ |
| `nvidia/nemotron-3-super-120b:free` | NVIDIA | Agentic, 1M context | ✅ |
| `openai/gpt-oss-120b:free` | OpenAI | General purpose | ✅ |
| `google/gemma-4-31b-it:free` | Google | Vision + tools | ✅ |

**Key facts:**
- ~20 RPM rate limit (stricter than Groq)
- Can use `openrouter/free` router for auto-selection
- Less predictable availability — models rotate
- Requires `langchain-openrouter` or `ChatOpenAI` with custom base URL

---

## Why We Chose Groq Over OpenRouter

This was the most important decision. Here's the full comparison:

### LangChain Integration Quality

| Feature | Groq | OpenRouter |
|---|---|---|
| Dedicated LangChain package | ✅ `langchain-groq` (official, well-maintained) | ⚠️ `langchain-openrouter` (newer, less mature) |
| `init_chat_model()` support | ✅ `init_chat_model("groq:model_name")` works natively | ❌ No native `model_provider="openrouter"` — must use `ChatOpenAI` with custom base URL |
| `bind_tools()` | ✅ Battle-tested, works reliably | ⚠️ Works via OpenAI compatibility layer but model-dependent |
| `with_structured_output()` | ✅ Supports both `method="json_schema"` and `method="function_calling"` | ⚠️ Works but may need defensive parsing |
| Async support (`ainvoke`) | ✅ Full support | ✅ Full support |

**Verdict:** Groq's LangChain integration is **significantly more reliable** for our use case (tool calling + structured output in an agentic loop).

### Environment Variable Conflicts

The original code uses `init_chat_model("openai:gpt-4.1")` which reads `OPENAI_API_KEY` and `OPENAI_API_BASE` from the environment. If we set `OPENAI_API_BASE=https://openrouter.ai/api/v1`, then **every** `openai:` prefixed call would go through OpenRouter — including calls that should be separate.

With Groq, there's no conflict. `init_chat_model("groq:llama-3.3-70b-versatile")` reads `GROQ_API_KEY` independently. The OpenAI env vars are left untouched.

### Rate Limits

| Provider | RPM (Requests Per Minute) | TPM (Tokens Per Minute) |
|---|---|---|
| **Groq** | ~30 RPM | ~300k TPM |
| **OpenRouter** | ~20 RPM | Less documented |

Our supervisor runs up to 2 parallel research agents. Each agent makes 3-5 LLM calls. Groq's 30 RPM gives us more headroom.

### Speed

Groq runs on custom LPU hardware — it's **dramatically faster** than any other inference provider. Typical response times:
- Groq: 50-200ms for first token
- OpenRouter: 500ms-2s+ depending on the underlying provider

For a multi-agent system with many serial LLM calls, this speed difference compounds massively.

### Availability

Groq's model catalog is stable — `llama-3.3-70b-versatile` has been available consistently. OpenRouter's free models rotate and can disappear without notice.

---

## Why These Specific Models

### `llama-3.3-70b-versatile` — The Workhorse

**Used for:** Research agent brain, Supervisor decisions, Brief generation, Research compression, Final report writing

**Why this model specifically?**

1. **70B parameters** — Large enough for complex reasoning, research synthesis, and multi-turn tool calling. Smaller models (8B, 32B) struggle with the agentic loops in our system.

2. **"Versatile" variant** — Groq's naming convention. This is the general-purpose variant optimized for a balance of speed, quality, and capability. It handles:
   - Tool calling (multiple tools, parallel calls)
   - Structured output (Pydantic schemas via `with_structured_output()`)
   - Long-form writing (research reports)
   - Following complex system prompts

3. **Proven track record** — Most widely used model on Groq. Extensive community testing with LangChain's `bind_tools()` and `with_structured_output()`.

4. **Context window** — 128k tokens context window. Our research messages can get long with multiple search results — 128k handles this.

**What about the newer/bigger models?**

| Alternative | Why NOT |
|---|---|
| `openai/gpt-oss-120b` | 120B params, but newer and less tested with LangChain tool calling patterns. May have quirks. |
| `moonshotai/kimi-k2-instruct` | 1T MoE model — cutting edge but very new (June 2026). Untested with our specific LangGraph patterns. Risk of instability. |
| `qwen/qwen3-32b` | Only 32B params. Might struggle with complex supervisor decisions and multi-tool calling. Good coding model but not as strong at general research. |

**Bottom line:** `llama-3.3-70b-versatile` is the **safe, proven choice** that balances quality, speed, and reliability. Once the system is stable, we can experiment with newer models.

### `llama-3.1-8b-instant` — The Speedster

**Used for:** Webpage summarization only

**Why this model specifically?**

1. **8B parameters** — Webpage summarization is a simple task: read raw HTML content, extract key facts, output structured JSON. You don't need 70B params for this.

2. **"Instant" speed** — This model runs at Groq's maximum speed. Since we summarize 3+ webpages per search call, speed matters a lot here.

3. **Structured output support** — Even the 8B model supports `with_structured_output()` for our `Summary` Pydantic schema. We use `function_calling` method which is more reliable on smaller models.

4. **Token efficiency** — Using the small model for simple tasks preserves our free tier quota for the important calls (research, supervision, report writing).

**Why not use 70B for everything?** Rate limits. If every call goes to `llama-3.3-70b-versatile`, we'll burn through 30 RPM quickly. Spreading load across models (70B for thinking, 8B for grunt work) maximizes throughput.

---

## The Changes Made

### Model Mapping (Before → After)

| File | Line | Before (Paid) | After (Free) |
|---|---|---|---|
| `research_agent.py` | 26 | `anthropic:claude-sonnet-4-20250514` | `groq:llama-3.3-70b-versatile` |
| `research_agent.py` | 28 | `openai:gpt-4.1-mini` | `groq:llama-3.1-8b-instant` |
| `research_agent.py` | 29 | `openai:gpt-4.1` (max_tokens=32000) | `groq:llama-3.3-70b-versatile` |
| `multi_agent_supervisor.py` | 71 | `anthropic:claude-sonnet-4-20250514` | `groq:llama-3.3-70b-versatile` |
| `research_agent_scope.py` | 32 | `openai:gpt-4.1` (temp=0.0) | `groq:llama-3.3-70b-versatile` (temp=0.0) |
| `research_agent_full.py` | 27 | `openai:gpt-4.1` (max_tokens=32000) | `groq:llama-3.3-70b-versatile` |
| `research_agent_mcp.py` | 56 | `openai:gpt-4.1` (max_tokens=32000) | `groq:llama-3.3-70b-versatile` |
| `research_agent_mcp.py` | 57 | `anthropic:claude-sonnet-4-20250514` | `groq:llama-3.3-70b-versatile` |
| `utils.py` | 42 | `openai:gpt-4.1-mini` | `groq:llama-3.1-8b-instant` |

### Dependencies Added

```toml
# pyproject.toml
"langchain-groq>=0.3.0"  # Required for init_chat_model("groq:...")
```

### Configuration Adjustments

- `max_concurrent_researchers`: **3 → 2** (to stay within Groq's ~30 RPM free tier)

---

## Rate Limit Strategy

With 2 parallel agents and ~30 RPM on Groq free tier:

```
Per research run (worst case):
├── Scoping: 1 call (clarify) + 1 call (brief) = 2 calls
├── Supervisor: ~3-4 calls (think + delegate + think + complete)
├── Agent 1: ~6-8 calls (search + think + search + think + compress)
├── Agent 2: ~6-8 calls (same)
├── Summarization: ~6-8 calls (3 webpages × 2 agents, using 8B model)
└── Final report: 1 call
────────────────────────────────
Total: ~25-31 calls over ~2-3 minutes
```

At 30 RPM, this is tight but workable. The calls are spread across time (agents run sequentially within their loop, only parallel between agents). The 8B summarization model calls are on a separate rate limit bucket.

**If you hit rate limits:** Groq returns 429 errors. LangChain has built-in retry logic. You may see slight delays but the system should self-recover.

---

## Potential Quality Tradeoffs

| Aspect | Claude Sonnet 4 / GPT-4.1 | Llama 3.3 70B |
|---|---|---|
| Tool calling reliability | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ (occasionally misses parallel tool calls) |
| Structured output | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ (very reliable with `function_calling` method) |
| Long-form writing | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ (good but slightly less polished prose) |
| Following complex prompts | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ (may need prompt adjustments for edge cases) |
| Research depth | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ (comparable for most topics) |
| Speed | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ (Groq LPU is blazing fast) |
| **Cost** | **💰💰💰** | **🆓** |

**The quality difference is small.** Llama 3.3 70B is one of the best open-source models available. For a research system, the difference between "excellent" and "slightly less excellent" is negligible — especially when the alternative is free.

---

## Future Upgrade Paths

When you want better quality (without paying), consider:

1. **`moonshotai/kimi-k2-instruct`** — 1T MoE model, recently added to Groq. Once it's more battle-tested with LangChain, it could be a significant upgrade.

2. **`openai/gpt-oss-120b`** — OpenAI's open-weight 120B model. Larger than Llama 70B, optimized for agentic tasks. Worth testing once the LangChain integration matures.

3. **`qwen/qwen3-coder`** on OpenRouter — If you ever need the MCP agent for code research, Qwen3 Coder has 1M context and excellent coding performance.

4. **Mix providers** — Use Groq for fast tool calling + OpenRouter as fallback for long-form writing. Would need custom logic to switch providers per task.
