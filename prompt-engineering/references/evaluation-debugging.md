# Evaluation, Debugging & Hallucinations

---

## Evaluation Frameworks

### SOMA — Designing LLM-as-Judge Rubrics

SOMA is not an output-quality checklist—it's a rule for how to *phrase the grading questions*
you give an LLM judge, so its scores are reliable:

- **S**pecific: ask concrete, narrow questions ("Does this cite at least one source for every
  factual claim?"), never a vague "is this good?"
- **O**rdinal: use a scaled answer (e.g. 1-5) with an explicit description per level, never a
  binary good/bad—binary judgments collapse nuance and are noisier.
- **M**ulti-**A**spect: ask a separate question per distinct quality dimension (relevance,
  truth, completeness, etc.—GitHub Copilot's "RTC" system) rather than one global "goodness"
  score that conflates everything.

**Critical caveat**: never let a model grade its own output—frame it as grading a third
party. Models get measurably worse at self-grading due to RLHF self-correction bias and
training-data self-promotion bias. Ground judge scores against multiple human annotators'
agreement (e.g. Kendall's Tau) rather than assuming the judge is valid.

**Evaluate the evaluator before trusting it at scale**: construct test cases with *known*
issues and known non-issues, run the LLM judge against them, and measure its false-positive
and false-negative rates first.

### Manual Review Checklist (4 dimensions)

Quick checklist for eyeballing individual outputs by hand:

- **Sufficiency**: Does the output fully address the request? All parts answered?
- **Order**: Is the output logically structured? Does it flow well?
- **Mechanics**: Grammar, spelling, punctuation, formatting correct?
- **Accuracy**: Are facts correct? Any hallucinations? Citations valid?

### Quantitative Metrics

| Metric | What it measures | Best for |
|--------|-----------------|----------|
| Accuracy | Correctness vs ground truth | Classification, extraction |
| BLEU/ROUGE | N-gram overlap vs reference | Summarization, translation |
| Embedding similarity | Semantic closeness | Open-ended generation |
| Format compliance rate | Valid JSON/YAML output | Production pipelines |
| Hallucination rate | % of invented facts | Factual tasks |
| Consistency | Stability across runs | Production reliability |

### Evaluation Methods (from simplest to most rigorous)

1. Blind prompting (eyeball one result)
2. Thumbs-up/down rating on 5-10 runs (use Jupyter widgets or simple CLI)
3. Blind A/B comparison between prompt variants
4. Elo rating via side-by-side comparison (Chatbot Arena approach)
5. Programmatic evaluation against predefined ground truth test cases
6. Model-as-judge (GPT-4 evaluating weaker model outputs, Vicuna-style)

### Online Evaluation

- **A/B test** prompt variants with real users.
- Track: task completion rate, satisfaction, time-to-complete, error rate, retry rate.
- **Monitor** in production: accuracy drift, latency spikes, cost anomalies.

---

## Debugging Workflow

When a prompt produces poor results, follow this sequence:

1. **Verify output format first**: Valid JSON? Correct structure? Format problems = weak format specification.
2. **Check for ambiguity**: Could the prompt be interpreted multiple ways?
3. **Test at temperature=0**: Cuts randomness. Fails at temp=0 = broken prompt. Fails only at higher temps = add constraints.
4. **Add one example**: If zero-shot fails, one example reveals if the description is the problem.
5. **Reorder content**: Move instructions before data. Move examples closer to input.
6. **Check context window**: Prompt + expected output fits?
7. **Check for contradictions**: "Be concise but thorough" is self-contradictory. Pick one.
8. **Reduce complexity**: Remove least important constraints, retest.

## Common Failure Modes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Won't stop listing/generating | temp too low, no stop sequence | Add stop sequences; raise temp |
| Hallucinated facts | No grounding; truth bias on false premise | Add RAG; "only use provided context" |
| Wrong format returned | Under-specified format; no examples | Add format spec + few-shot in target format |
| Ignores instructions | Instructions at end; lost in context | Move to beginning; simplify; use system msg |
| Truncated/incomplete output | max_tokens too low | Increase max_tokens; ask model to check |
| Overly verbose/chattiness | Chat model bias | "Respond concisely. No commentary. Just the answer." |
| Refuses reasonable request | Over-alignment; safety filters | Rephrase without trigger words |

---

## Hallucination Management

### Why Hallucinations Occur

- Model is a training data mimic, not a knowledge base. Can't fact-check itself.
- Truth bias: Prompt is assumed to be true; false premises won't be corrected.
- "Don't make stuff up" doesn't work as an instruction—the model doesn't distinguish fact from fiction internally.

### Mitigation Strategies

1. **RAG grounding**: "Answer ONLY based on the provided context."
2. **Source citation**: "Cite specific passages." Makes verification possible.
3. **Confidence expression**: "If uncertain, state your confidence level (high/medium/low)."
4. **Chain-of-thought verification**: "Show your reasoning, then verify your answer."
5. **External fact-checking**: Run output through a separate verification step.
6. **Reference text injection**: Include authoritative text in the prompt.
7. **Self-evaluation**: "Review your answer. Is every fact supported by the context?"
8. **Temperature=0**: Reduces randomness but doesn't eliminate hallucinations—an incorrect token may still be the most likely one.
9. **Induced hallucinations**: False facts in the prompt produce false outputs. The model assumes its prompt is factual.

### The "Trust but Verify" Principle

Structure outputs so facts can be verified: ask for reasoning traces, source citations, calculations that can be independently computed, and searchable keywords/details.
