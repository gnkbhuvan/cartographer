# Evaluation

RAG quality has three independent failure surfaces. Evaluate each one — a single
end-to-end "looks good" check hides which stage actually broke.

## 1. Retrieval Quality

| Metric | What it measures | Use when |
|---|---|---|
| **Context precision** | % of retrieved chunks that are actually relevant | Always — cheap, can be scored by an LLM judge alone |
| **Context recall** | % of all relevant chunks in the corpus that were retrieved | When you can afford exhaustive annotation — harder to measure but catches "missed the right document entirely" failures precision can't |
| **NDCG / MAP / MRR** | Whether the *order* of retrieved results is good, not just membership | Rank order matters for downstream use (e.g., showing a ranked list to a user, not just feeding generation) |

For embedding model selection specifically, benchmark against your own data using MTEB-style
task categories (retrieval, classification, clustering) rather than trusting a generic
leaderboard score. For retrieval-algorithm benchmarking (ANN index choices), evaluate
recall, queries-per-second, build time, and index size together — they trade off against
each other (a more accurate index is typically slower/heavier to build).

## 2. Generation Quality

- **Faithfulness / hallucination rate**: does the generated answer only use facts present in
  the retrieved context? Target a low single-digit percentage or better for production.
- **Answer relevance**: does the answer actually address the question, independent of
  whether it's factually grounded?
- Use citation requirements (ask the model to cite which retrieved passage supports each
  claim) to make faithfulness mechanically checkable, not just judged by feel.

## 3. End-to-End Production KPIs

Representative production targets (calibrate to your domain, but use these as a sanity
floor): context precision ≥ 0.9, context recall ≥ 0.8, hallucination rate ≤ 0.05, answer
relevance ≥ 0.9, mean query latency in the low seconds with controlled p95 tail latency,
uptime ≥ 99.9%.

**Monitor query volume after launch as a quality signal**: a spike followed by a sharp drop
in the first 2-3 weeks usually means the system isn't answering well enough and users are
reverting to their old workaround — not that interest faded.

## Tooling

**LangSmith** (LangChain's evaluation/observability platform) is the most direct fit for RAG
eval regardless of whether you adopted the LangChain framework itself: it supports
heuristic checks, LLM-as-judge evaluators scored against criteria you define, pairwise
comparisons, and human annotation queues — and separates retrieval-quality scoring
(context precision/faithfulness) from generation scoring in its tutorials.

For retrieval-specific benchmarking methodology (independent of any one platform), BEIR-style
evaluation across multiple standard retrieval benchmarks is the closest thing to a standard
harness design if you're building your own.

## Build the Harness Before Launch, Not After

"You can't fix what you can't measure." Stand up the evaluation harness — even a small
manually-curated set of 20-50 representative query/expected-context/expected-answer
triples — before going to production, not as a reaction to a quality complaint after
launch. See the `prompt-engineering` skill for the general LLM-as-judge rubric design
principles (specific, ordinal, multi-aspect questions; never let a model grade its own
output) — those apply directly to the generation-quality leg here.
