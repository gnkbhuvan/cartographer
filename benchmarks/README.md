# Cartographer Benchmarks

*Automated evaluation of the 4 AI skills: prompt-engineering, agentic-ai, fastapi-genai, production-rag.*

## Quickstart

```bash
# 1. Validate instruments (no API, no spend) — ALWAYS RUN FIRST
python benchmarks/selftest.py

# 2. Validate behavioral probes (no API)
python benchmarks/behavior.py --selftest

# 3. Validate LLM judge (small API spend, ~$0.02)
#    Requires ANTHROPIC_API_KEY in .env or env var
python benchmarks/judge.py --selftest

# 4. Run the full evaluation (API spend)
#    python benchmarks/runner.py --all --runs 5
```

## How it works

See `SKILL-EVALUATION-FRAMEWORK.md` for the full methodology. Quick summary:

1. **Selftest** validates every scorer — good reference passes, bad reference fails on its declared axis
2. **Behavioral gates** verify each skill actually changes agent behavior (not just carries text)
3. **Deterministic correctness** checks each skill produces correct answers to tasks with right answers
4. **LLM judge** scores subjective axes (clarity, reasoning depth) with a validated rubric
5. **Comparative baselines** run the same tasks with no skill vs. your skill vs. naive instructions

## Architecture

```
benchmarks/
├── selftest.py       ← Validates scorers before API spend
├── behavior.py       ← Behavioral gate probes (deterministic)
├── judge.py          ← LLM-as-judge rubric scoring
├── tasks.py          ← 8 task definitions (2 per skill)
├── runner.py         ← Full harness (WIP)
└── results/          ← Timestamped output directories
```

## Tasks

| ID | Skill | What it tests |
|----|-------|---------------|
| pe-clarify | prompt-engineering | Asks clarifying questions before writing prompts |
| pe-debug | prompt-engineering | Diagnoses root cause, not superficial patch |
| ag-necessity | agentic-ai | Questions whether an agent is needed |
| ag-tools | agentic-ai | Proposes minimal, non-overlapping tool set |
| fa-lifespan | fastapi-genai | Uses lifespan for model loading |
| fa-ratelimit | fastapi-genai | Uses per-user rate limiting |
| rag-necessity | production-rag | Questions whether RAG is needed |
| rag-vectordb | production-rag | Recommends reusing existing infra |

## References

- [SKILL-EVALUATION-FRAMEWORK.md](../SKILL-EVALUATION-FRAMEWORK.md) — Full methodology and research foundation
- [Ponytail benchmarks](https://github.com/DietrichGebert/ponytail/tree/main/benchmarks) — The inspiration
- [Hebbia's evaluation framework](https://www.hebbia.com/blog/evaluating-ai-agents-a-hybrid-deterministic-and-rubric-based-framework)
- [arXiv:2507.21504](https://arxiv.org/abs/2507.21504) — Survey on LLM Agent Evaluation
