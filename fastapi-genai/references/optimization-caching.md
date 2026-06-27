# Optimization & Caching

Apply the "don't add infrastructure before you've measured you need it" axiom here
specifically: start with the cheapest applicable technique below and escalate only when a
measured cost/latency number justifies the next one.

## Caching — Escalation Ladder

1. **Exact-match (keyword) cache**: cache by exact prompt/parameters. Cheapest, works well
   for genuinely repeated queries.
   ```python
   from fastapi_cache.decorator import cache

   @router.post("/classify")
   @cache(expire=60)
   async def classify_document(title: str) -> str: ...
   ```
2. **Semantic cache**: embed the query, cache-hit on similarity above a threshold rather
   than exact match. Justified once exact-match hit rate is low because users phrase the
   same question differently — typical reported hit-rate gains are 60-70% on Q&A-style
   traffic once this is warranted.
   ```python
   class SemanticCacheService:
       def __init__(self, threshold: float = 0.35):
           self.threshold = threshold  # tune empirically against your own traffic

       async def ask(self, query: str) -> str | None:
           vector = embed(query)
           if hit := await self.cache_db.search(vector, limit=1):
               if hit[0].score <= self.threshold:
                   return hit[0].payload["response"]
           return None  # caller falls through to a real model call, then caches it
   ```
3. **Provider-native context/prompt caching**: when a large, reused system prompt or
   document set is sent on every call, mark it cacheable (e.g., Anthropic's
   `cache_control: {"type": "ephemeral"}` on a system block) so the provider doesn't
   re-process it each time. This cuts cost and latency on the *repeated context*, not the
   per-call token count — don't expect it to shrink your bill if the context isn't actually
   reused across calls.

**Eviction policy**: start with LRU; only move to LFU/FIFO if you've measured LRU
performing badly for your access pattern.

## Batching

For non-real-time, high-volume workloads, use the provider's batch API rather than firing
individual requests — commonly near 50% cheaper, at the cost of results arriving
asynchronously (not suitable for an interactive chat endpoint).

```python
request = {"custom_id": str(uuid4()), "method": "POST", "url": "/v1/chat/completions",
           "body": {"model": model, "messages": messages}}
# write N such lines to a .jsonl file, then:
file = await client.files.create(file=open("batch.jsonl", "rb"), purpose="batch")
job = await client.batches.create(input_file_id=file.id, endpoint="/v1/chat/completions", completion_window="24h")
```

## Quantization (Self-Hosted Models Only)

| Precision | Trade-off |
|---|---|
| FP16 | ~2x memory savings, minimal quality loss — safe default |
| BFLOAT16 | Similar to FP16, different numerical behavior |
| INT8 | Large savings (~50% on typical models), noticeable quality loss — validate against your eval set before shipping |
| INT4 | For constrained/edge deployment; real accuracy risk |

Only relevant if you're self-hosting a model at all — this doesn't apply when calling a
hosted provider API.

## Fine-Tuning — When It's Actually Worth It

Consider fine-tuning only when: token usage is high specifically *because* of a long
repeated system prompt/examples that fine-tuning could absorb into the weights, the task
is domain-specific and stable, or per-request latency from a large prompt is itself the
bottleneck. Don't reach for it as a first lever — it's the most expensive escalation on this
page, and prompt engineering or caching usually gets most of the win for much less cost
(see `prompt-engineering`'s fine-tuning decision tree for the full criteria).

## Cost/Latency Levers, Roughly Ordered by Effort

1. Add an exact-match cache.
2. Stream responses so perceived latency drops even if total compute doesn't.
3. Add a semantic cache if exact-match hit rate is measured to be low.
4. Switch to a batch API for anything non-interactive.
5. Use provider-native context caching for large reused context.
6. Only then: quantization (self-hosted) or fine-tuning.
