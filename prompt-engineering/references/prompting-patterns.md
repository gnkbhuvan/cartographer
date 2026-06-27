# Prompting Patterns — Detailed Reference

For the pattern dispatch table (when to use which pattern), see the "Choosing a Prompting
Pattern" table in `SKILL.md`. This file holds templates and worked detail only.

---

## Chain-of-Thought Details

CoT is the model's only mechanism for "reflection." The transformer can only pass higher-layer insights to lower layers through generated tokens. By outputting intermediate reasoning tokens, the model gives future tokens something to attend to—simulating multi-step deliberation.

**Zero-shot CoT**: Append `"Let's think step by step."`

**Few-shot CoT**: Provide examples with explicit reasoning traces.

**Self-consistency**: Run CoT multiple times at temp>0. Take the majority answer across reasoning paths.

**When CoT is essential**: Math problems, logical deduction, multi-step instructions, planning tasks.

## ReAct Pattern

```
Thought: I need to find out X.
Action: search("X")
Observation: [search results about X]
Thought: Based on this, I should calculate Y.
Action: calculate("Y")
Observation: [result of Y]
Thought: I now have the answer.
Final Answer: [answer]
```

The model alternates reasoning with tool calls. Each observation is fed back into the prompt for the next reasoning step.

## RAG Prompt Template

```
Use ONLY the following context to answer the question.
If the answer is not in the context, say "I don't have enough information."
Cite specific passages with [1], [2] notation.

Context:
[1] {chunk1}
[2] {chunk2}

Question: {question}
Answer:
```

**Chunking considerations**: Size to balance context vs. focus. 10-20% overlap to prevent splitting key information. Retrieve 3-10 chunks. Re-rank for relevance. Each chunk should fit the embedding model's window and contain exactly one main idea—don't blend multiple topics into one vector.

**Retrieval method — lexical vs. neural**:
- **Lexical** (TF-IDF, BM25, Jaccard): fast, debuggable, no precompute, tunable per-field boosting. Use when matches are mostly keyword/exact-term based, or when you need to explain why a result matched.
- **Neural** (embeddings + vector store): catches synonyms, paraphrases, cross-language matches—"based on ideas, not words." Use when queries and documents rarely share exact wording. Harder to debug when a match is wrong.

**Chekhov's gun fallacy**: the model over-interprets *anything* placed in the prompt as relevant—"if you hang a pistol on the wall, it should be fired." A poorly-matched retrieved chunk doesn't just get ignored; it actively misleads the completion. A bad retriever is worse than no retriever. Filter/re-rank before inserting, don't rely on the model to notice irrelevance on its own.

## Tree of Thoughts (ToT)

Branches reasoning into multiple parallel paths instead of one linear chain, evaluates each
branch, and can backtrack—unlike CoT, which commits to one path token by token.

```
Generate 3 distinct approaches to solve: {problem}
For each approach, evaluate: is this likely to succeed? (sure / maybe / impossible)
Expand only the "sure" and "maybe" branches one step further.
Repeat until a branch reaches a solution or all branches are pruned.
Select the best completed branch.
```

**When to escalate to ToT**: only after CoT plateaus on a genuinely combinatorial/search-like
problem. Benchmark gap that justifies the extra cost: GPT-4 + CoT scores 4% on "Game of 24";
GPT-4 + ToT scores 74%. For tasks with one clear reasoning path, ToT adds cost with no benefit—use CoT.

## Structured Output & Tool-Call Templates

### JSON Output

```
Only return valid JSON. Never include backtick symbols such as: `
The response will be parsed with json.loads().
Use this exact schema:
{
    "field1": "type/description",
    "field2": ["array description"],
    "field3": {"nested": "description"}
}
```

### Function Calling / Tool Use

```
You have access to the following tool:
- search(query: str) -> list[dict]: Search the knowledge base.

When you need to search, respond with:
{"tool": "search", "query": "..."}

When you have the answer, respond with:
{"answer": "..."}
```

### Guarding Against Hallucinations (quick version—full list in `evaluation-debugging.md`)

- "Answer ONLY based on the provided context. If the context doesn't contain the answer, say 'I don't have enough information.'"
- "Cite specific passages using [1], [2] notation."
- Use RAG to ground outputs in retrieved facts rather than the model's parametric memory.

## Few-Shot Example Selection

- **Static**: Pre-curated set covering representative cases.
- **Semantic similarity**: Embed the input, retrieve similar examples from vector store.
- **Diversity sampling**: Maximize variety among selected examples to cover more ground.
- **Length-based**: Choose shorter examples to fit more; fall back to longer for edge cases.

## GPT Prompting Tactics

- **Avoid hallucinations with reference text**: "Use the provided documents. Cite sources."
- **Give thinking time**: "Before answering, consider..."
- **Inner monologue**: Have model output private reasoning in a structured section you can parse out before showing to the user.
- **Self-eval**: Ask model to evaluate its own output against explicit criteria.
- **Majority vote** (classification): Run N times at temp>0, take the most common result.

## Prompt Chaining (LangChain patterns)

- **Sequential**: A → B → C (each depends on previous output).
- **Parallel fan-out**: A → [B, C, D] simultaneously → combine results.
- **Conditional**: If condition X then B else C.
- **Stuff**: Everything in one prompt.
- **Refine**: Iteratively summarize, refining across chunks.
- **Map-Reduce**: Summarize chunks independently, then summarize summaries.
- **Map-Re-rank**: Summarize chunks, score relevance, combine top-ranked.
