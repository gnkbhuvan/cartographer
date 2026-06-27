# Build vs. Buy

Two separate decisions get conflated under "should I use a framework." Make them
separately.

## Decision 1: Framework or Native Provider SDK?

**Default to the provider's native SDK first** — it's the dependency you don't have to add.

- **OpenAI**: the Responses API ships File Search — a native vector store with built-in
  query optimization and reranking. A single-provider RAG pipeline on OpenAI can often skip
  LangChain/LlamaIndex entirely for ingestion and retrieval.
- **Anthropic**: the Claude Agent SDK gives you the agent loop and tool execution, but has
  no native vector store — on a Claude-only stack you're choosing between rolling your own
  (embeddings API + a vector store from `vector-db-selection.md`) or adopting a framework
  for convenience, not necessity.

**Reach for a framework (LangChain, LlamaIndex, etc.) only when you need**:
- Multi-provider portability — swapping models/providers without rewriting the pipeline.
- A large document-loader/connector ecosystem (dozens of source-format integrations) rather
  than the handful your own ingestion code would need.
- Complex chain composition (map-reduce summarization, multi-step agentic RAG) where
  hand-rolling the orchestration would reinvent retries, state, and error handling the
  framework already solved.
- Observability/eval tooling (e.g., LangSmith) with no equivalent already in your stack.

If none of those apply, a framework is a dependency added for what a native SDK call and a
few lines of glue code already cover.

## Decision 2: DIY Components or a Turnkey RAG Platform?

This is a different axis: even if you're writing your own code (Decision 1), you can still
buy a **turnkey platform** that bundles extraction, parsing, retrieval, hallucination
detection, and compliance into one vendor relationship instead of assembling best-of-breed
pieces yourself.

| | DIY (assemble components yourself) | Turnkey (single vendor) |
|---|---|---|
| **Cost predictability** | Initial estimates are notoriously unreliable — actual production spend commonly runs 3-5x over the original projection | Simplified, more predictable cost structure |
| **Flexibility** | Full control over every component | Locked into the vendor's choices for bundled pieces |
| **Operational overhead** | You coordinate every vendor's SLA and support process yourself when something breaks | "One throat to choke" — single point of accountability |
| **Talent requirement** | Needs ML engineering + data engineering + MLOps + security/compliance skill all in-house | Lower in-house skill requirement for the bundled parts |

**Recommended default**: hybrid. Use turnkey/managed services for the
**non-differentiating** plumbing (generic extraction, parsing, basic compliance) and keep
**your actual differentiator** — domain-specific retrieval logic, your data, your
evaluation criteria — in-house. Don't outsource the part of the system that's supposed to
be your edge.

## Putting Both Decisions Together

A reasonable production-RAG default for most teams: native provider SDK (Decision 1) +
reused existing database from `vector-db-selection.md` + DIY on your core retrieval logic,
with turnkey/managed services only for ingestion plumbing you don't want to maintain
(Decision 2). Escalate either axis only when a specific, named requirement forces it — not
preemptively.
