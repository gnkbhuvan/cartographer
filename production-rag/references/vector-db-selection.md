# Vector Database Selection

## The First-Principles Rule

**Default to the database you already operate.** Adding a dedicated vector database is a
new piece of infrastructure with its own ops burden, billing relationship, and failure
mode. Most teams below tens of millions of vectors don't need one.

- **Already on Postgres?** Add `pgvector`. It's the cheapest option at every scale below
  roughly 10-50M vectors, supports HNSW indexing, gives you full ACID guarantees, and SQL
  joins against the rest of your application data — none of which a dedicated vector store
  gives you. Zero new infrastructure, zero new licensing cost.
- **Already on MongoDB?** Use Atlas Vector Search. Same logic: removes an entire category
  of engineering complexity by staying inside infrastructure you already run, manage, and
  pay for.
- **On Supabase already, or want managed Postgres with auth built in?** Supabase's managed
  pgvector adds auth, row-level security, and edge functions on top — useful if you also
  need per-user access control on top of retrieval (see `production-hardening.md`).

**Only move to a dedicated vector database when you hit a real ceiling**: vector count well
beyond what pgvector/Atlas handle comfortably, or a specific capability your current
database lacks (e.g., very low single-digit-millisecond p50 latency at huge scale, or
hybrid search quality your current setup can't match).

## Dedicated Vector Database Comparison

| Database | Best for | Trade-off |
|---|---|---|
| **Pinecone** | Zero-ops prototyping; teams that don't want to think about infrastructure | Usage-based pricing (storage + queries + compute) — costs grow quickly with scale; 3-8x a Postgres-based option at the same vector count |
| **Qdrant** | Lowest latency (benchmarks show ~4ms p50); both managed and self-hosted | Resource-based pricing — predictable for steady load, less efficient for spiky traffic |
| **Weaviate** | Native hybrid search (vector + keyword) without bolting it on yourself | Resource-based pricing, similar profile to Qdrant |
| **pgvector / Atlas / Supabase** | Reusing existing infrastructure, ACID + joins, lowest cost at small-to-mid scale | Ceiling around 10-50M vectors; less specialized recall tuning than a dedicated engine |

**Pure vector search is not enough in production** for most use cases — proper nouns,
product codes, and exact-match queries fail under pure semantic search. If you go with a
dedicated store, prefer one with native hybrid search (Weaviate, Qdrant) over bolting
keyword search on yourself, unless you're already happy maintaining that combination at the
pgvector/Elasticsearch layer.

## Budgeting

Vector database spend commonly runs **1/5 to 1/2 of total model API cost** once a system is
in production — budget for storage + embedding + query cost as its own line item, not an
afterthought to generation cost. At roughly 1M vectors with moderate query load, expect
something in the tens to low-hundreds of dollars per month for a managed dedicated service;
reusing existing Postgres/Mongo infrastructure is typically cheaper still since there's no
new bill at all.

## Re-evaluate, Don't Re-architect by Default

Switching embedding models requires re-embedding (and re-indexing) your entire corpus — this
is the most expensive "small" decision in the stack. Don't chase every marginal embedding
quality improvement; require a meaningful, measured gain (via your eval harness, see
`evaluation.md`) before paying that cost.
