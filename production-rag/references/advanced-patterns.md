# Advanced Patterns

Plain RAG (embed → retrieve → generate, once) is the default. Each pattern below is an
escalation — adopt it only when plain RAG demonstrably fails on a specific class of query,
not preemptively. Each adds real cost and failure surface.

## Agentic RAG

**What it is**: instead of one retrieve-then-generate pass, an agent can re-retrieve and
refine when the first pass wasn't sufficient, call external tools (web search, APIs) beyond
the pre-ingested corpus, and decompose a complex query into sub-queries it answers and
combines.

**Use when**: queries are multi-part or require connecting information that a single
retrieval pass can't gather at once (e.g., "compare X and Y across three different
documents and summarize the difference").

**Don't use when**: queries are single-fact lookups — agentic overhead (more LLM calls,
more latency, more cost, more failure surface) buys nothing over plain RAG there, and
compounding error across the extra steps makes reliability worse, not better. See the
`agentic-ai` skill for the full reliability math and the architecture of when/how to build
this (planning, tool use, failure modes) — this entry is the RAG-specific trigger for
reaching into that skill.

## Multimodal RAG

**What it is**: retrieving non-text content (images, tables, charts) alongside or instead of
text.

Two approaches:
1. **Convert to text**: caption images, describe charts, then run the standard text RAG
   pipeline. Simplest; loses information the caption didn't capture.
2. **Shared embedding space**: use a multimodal embedding model (e.g., CLIP-style) that
   embeds text and images into the same vector space, so a text query can retrieve
   relevant images directly without an intermediate captioning step.

**Use when**: the source corpus is meaningfully visual (diagrams, product photos, charts)
and text-only retrieval would miss what the user actually needs.

## RAG with Tabular Data

**What it is**: text-to-SQL pattern — an LLM converts the natural-language query plus the
table schema into SQL, executes it, and generates a response from the result, rather than
trying to retrieve table rows via embedding similarity (which doesn't work well for
structured aggregation queries like "how many units sold in the last 7 days").

**Use when**: the underlying data is genuinely tabular/relational and the question requires
aggregation, filtering, or joins — not when a table is small enough to just describe in
text and embed normally.

**Watch for**: with many tables, add an intermediate step that first identifies which
table(s) are relevant before generating SQL against all of them.

## Graph RAG (Knowledge-Enhanced RAG)

**What it is**: extract entities and relationships from the corpus during ingestion to
build a knowledge graph, enabling multi-hop reasoning — connecting facts across documents
to reach a conclusion no single retrieved chunk states directly.

**Use when**: questions require connecting different pieces of information across documents
to reach a conclusion that isn't stated in any one place — flat vector/keyword retrieval
fundamentally can't do this because it retrieves chunks independently, not relationships
between them.

**Don't use when**: questions are answerable from a single document or chunk — the
knowledge-graph construction and maintenance cost isn't justified, and it adds an entire
new ingestion pipeline (entity/relationship extraction) to keep correct as the corpus
changes.

## RAG vs. Long Context — Re-check the First Axiom

Before reaching for any pattern above, re-confirm the system actually needs RAG at all: if
the relevant knowledge base is small and stable (roughly under 200K tokens / ~500 pages),
putting it directly in context is simpler and has none of RAG's retrieval-quality failure
surface. Advanced RAG patterns solve problems that only exist once you've correctly
concluded RAG itself is necessary.
