# Production Hardening

## Total Cost of Ownership

**Direct costs**: embedding model + generation LLM API fees, content extraction/parsing
tools, reranking, hallucination-detection components, security/compliance tooling.

**Indirect costs** (the ones teams underestimate): vector database spend (often 1/5 to 1/2
of model API cost — see `vector-db-selection.md`), compute/storage for staging and
production environments, integration overhead with existing enterprise systems, DevOps and
monitoring, disaster recovery, ongoing security audits.

**Reality check**: initial DIY cost estimates commonly run 3-5x over the original
projection once in production. Budget with that multiplier in mind, or weight the
build-vs-buy decision (`build-vs-buy.md`) toward turnkey for components where that
uncertainty is unacceptable.

## Security & Compliance

- **Encryption**: at rest and in transit, across every stage — extraction, chunking,
  embedding, and storage in the vector database, not just the final response.
- **Access control via retrieval-time filtering**: add permission metadata fields at
  ingestion time and filter by them at query time — this is RAG's structural advantage over
  fine-tuning (axiom 2 in `SKILL.md`). Don't rely on prompt instructions to enforce access
  control; enforce it in the retrieval query itself.
- **PII/PHI handling**: redact sensitive fields during ingestion, but verify redaction
  doesn't quietly degrade answer quality — test both directions.
- **External LLM data leakage**: sending retrieved context to a third-party LLM API carries
  data-residency risk. For regulated data, consider on-premise/VPC-hosted open models
  instead of an external API call, and confirm with the user which compliance regime
  applies (HIPAA/SOC 2/GDPR) before defaulting to a hosted provider.
- **Prompt injection from retrieved content**: treat retrieved documents as untrusted input,
  not just the user's query — a malicious or compromised document in the corpus can attempt
  to inject instructions via the same channel as legitimate context. Sanitize/validate
  retrieved content and keep output content-filtering in place regardless of source.

## Latency

- Computational load comes from semantic search + hybrid search + reranking + generation
  combined — profile each stage separately, not just total response time.
- Control **tail latency (p95)** specifically, not just the mean — a fast average with a
  slow tail still produces a bad user experience for a meaningful fraction of queries.
- Mitigations: parallelize independent stages, cache repeated/similar queries, use
  approximate (not exact) nearest-neighbor search at scale, auto-scale under load, and
  reconsider model/hardware choice if a stage is consistently the bottleneck.

## Monitoring

Track, continuously, not just at launch: query volume (a post-launch drop-off is a quality
signal, not just declining interest — see `evaluation.md`), latency distribution including
p95/p99, retrieval and generation quality metrics from the eval harness, and user feedback
where available. Strong observability is what turns "something's wrong" into "stage 3 is
the bottleneck" fast enough to fix before it compounds.

## Common Failure Modes

| Symptom | Likely cause | Fix |
|---|---|---|
| Confidently wrong/missing answers despite content existing in the corpus | No relevant data was actually retrieved | Check corpus coverage for that query class; expand ingestion |
| Retrieval quality degrades as the corpus grows | Pure vector or pure keyword search without hybrid/reranking | Add hybrid search and a reranking stage (`pipeline-stages.md`) |
| Hallucination despite good retrieval | Generation doesn't faithfully use the retrieved context, or context is incomplete/ambiguous | Add explicit "answer only from context" instructions, citation requirements, and faithfulness checks |
| Inconsistent answer quality across query types | Prompt under-tested against query diversity | Test the generation prompt against a broad, representative query set, not a handful of happy-path examples |
| Vendor coordination chaos when something breaks | Too many DIY point-solution vendors with separate SLAs | Revisit the turnkey option for non-differentiating components (`build-vs-buy.md`) |
