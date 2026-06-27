# Pipeline Stages — Detailed Reference

The RAG pipeline has two flows: **ingest** (parse → chunk → embed → index) and **query**
(embed query → retrieve → rerank → generate). Each stage below has its own decision space.

---

## Parsing & Ingestion

Extract text from source formats (PDF, Word, PowerPoint, HTML, Notion/Confluence/Jira
exports, databases). Use entity/relationship extraction here too if you're building toward
Graph RAG (see `advanced-patterns.md`).

**Watch for**: tables, multi-column layouts, and scanned/image-only PDFs need
format-specific extraction, not plain text scraping—plain extraction silently mangles
table structure and loses scanned-page content entirely.

## Chunking

| Strategy | How it works | Trade-off |
|---|---|---|
| **Fixed-size** | Split by characters/words/sentences/paragraphs (e.g., 2,048 chars) | Fast and simple; arbitrarily cuts semantic boundaries |
| **Recursive** | Split hierarchically (sections → paragraphs → sentences) until each piece fits the size limit | Reduces boundary-cutting losses vs. fixed-size |
| **Semantic** | Split at topic/meaning boundaries rather than fixed length | Preserves one-idea-per-chunk; costs more to compute |
| **Domain-specific** | Code splitters, Q&A-pair splitters, language-aware splitters | Matches structure of the source content |
| **Token-based** | Chunk by the generation model's own tokenizer | Aligns with the downstream model; forces re-indexing if you switch models |

**Overlap**: add a small overlap (e.g., 20 characters on a 2,048-character chunk) so
information isn't lost exactly at a boundary.

**Chunk size trade-off**: smaller chunks fit more distinct pieces of information into a
fixed context budget but lose cross-chunk context and double indexing/embedding compute
when halved; larger chunks preserve context but retrieve fewer distinct facts per query.
**There is no universal best size—experiment against your own eval set.**

**One main idea per chunk**: don't let a single chunk blend multiple topics—it produces a
muddy embedding vector that matches everything and nothing well.

## Embedding

- Pick an embedding model and commit to a re-indexing plan: switching embedding models
  means re-embedding your entire corpus, not just new documents.
- Benchmark candidate embedding models against your own data using MTEB-style task
  categories (retrieval, classification, clustering) rather than trusting a single
  leaderboard number out of context.
- A 5% quality improvement from a new embedding model isn't automatically worth adopting—
  check its latency and hardware requirements (GPU class) before swapping.

## Retrieval

**Term-based (sparse) retrieval**:
- TF-IDF: term frequency × inverse document frequency.
- BM25 (and BM25+/BM25F variants): TF-IDF with document-length normalization. Strong
  out-of-the-box baseline, cheap, fast to index and query.
- Pros: exact-match strength (error codes, product names, proper nouns). Cons: no synonym
  or paraphrase matching.

**Embedding-based (dense) retrieval**:
- Convert query and documents to vectors with a shared embedding model; retrieve by cosine
  similarity / nearest neighbor.
- At scale, exact nearest-neighbor search is too slow—use **approximate nearest neighbor
  (ANN)** instead:
  - **HNSW** (Hierarchical Navigable Small World): high accuracy, fast queries, slow and
    memory-heavy to build.
  - **LSH** (locality-sensitive hashing): fast, low-memory build; trades accuracy for speed.
  - **IVF** (inverted file / clustering): cluster vectors, search nearest clusters first.
  - **Product Quantization**: compress vectors into lower-dimensional subvectors to cut
    memory.
  - Libraries: FAISS, ScaNN, Hnswlib, Annoy.
- Pros: semantic/paraphrase matching, natural-language queries. Cons: slower queries,
  embedding + storage cost, obscures exact keyword matches.

**Hybrid search** (combine both): pure vector search fails on proper nouns, exact codes,
and short exact-match queries—production RAG generally needs hybrid search, not pure
vector search alone.
- **Sequential**: cheap term-based retriever (BM25) pulls candidates → reranker refines.
- **Ensemble / Reciprocal Rank Fusion (RRF)**: run retrievers in parallel, fuse rankings:
  `Score(D) = Σ 1/(k + rank_i(D))`, with `k ≈ 60`.

## Reranking

Refine the initial candidate set for precision. Options beyond pure relevance: time-decay
reranking (upweight recent documents for news/support-ticket use cases). For *generation*
context (not search ranking), inclusion matters more than precise order—but don't bury the
most important chunk in the middle of a long context window (the `prompt-engineering`
skill calls this the "Valley of Meh").

## Contextual Retrieval (Boosting Chunk Quality Pre-Index)

Augment chunks before embedding/indexing them, rather than only tuning retrieval after:
- **Metadata tagging**: keywords, extracted entities, source/date — usable for filtering
  (also your access-control mechanism, see `production-hardening.md`).
- **Document context prefix**: prepend the source document's title/summary to each chunk so
  it isn't orphaned from its parent context.
- **Situating context**: have an LLM generate a 50–100 token note explaining where this
  chunk fits within its source document, prepended before indexing — meaningfully improves
  retrieval for chunks that read as ambiguous in isolation.
- **Q&A reformatting**: some teams get their best results by re-organizing source content as
  question-answer pairs before indexing, since user queries are themselves questions.

## Query Rewriting

Rewrite ambiguous or context-dependent queries into stand-alone form before retrieval
(e.g., resolve "How about Emily Doe?" into "When did Emily Doe last buy from us?" using
conversation history). Risk: rewriting can hallucinate intent if the reference is genuinely
unclear — when uncertain, surface the ambiguity rather than guessing.

## Generation

Standard prompt-engineering concerns apply directly here — see the `prompt-engineering`
skill for prompt structure, hallucination guarding, and citation requirements. RAG-specific
addition: instruct the model to answer **only** from retrieved context and to say so
explicitly when the context doesn't contain an answer, rather than falling back to its
parametric memory.
