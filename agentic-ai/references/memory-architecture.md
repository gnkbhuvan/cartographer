# Memory Architecture

## Three Kinds of Memory

| Kind | What it is | Persistence | Use for |
|---|---|---|---|
| **Internal/parametric** | What's baked into the model's weights | Permanent until retrained/fine-tuned | Stable, general knowledge — not user- or session-specific facts |
| **Short-term** | The current context window | One task/session | What the agent is actively working on right now |
| **Long-term** | External storage (database, vector store, knowledge graph) | Persists across sessions | Facts that should outlive a single conversation: user preferences, prior decisions, accumulated history |

The context window is a limited, costly resource — give it everything the current step
needs and nothing more. Don't default to "include the whole history" when a targeted
retrieval from long-term memory would do.

## Building Long-Term Memory

- **Rolling context window**: simplest — keep recent turns, eject the oldest when the
  window fills. No semantic prioritization, so important early information (the original
  task goal) can get silently dropped purely because it's old, not because it's unimportant.
- **Keyword-based memory**: extract and index keywords from each turn, retrieve by keyword
  match later. Simple, preserves topical continuity, but misses semantically-related
  content that doesn't share exact keywords.
- **Semantic/vector memory**: embed interactions, retrieve by similarity at query time. See
  the `production-rag` skill for the retrieval-mechanics side of this — agent memory and
  RAG retrieval are the same underlying problem applied to different content (prior
  interactions vs. a document corpus).
- **Graph memory**: extract entities/relationships into a knowledge graph for multi-hop
  recall ("what did this user previously say about X, and how does that relate to Y").
  Justified only when an agent genuinely needs to connect facts across many past
  interactions — it's a real ongoing maintenance cost (the `production-rag` skill covers
  the same trade-off applied to documents).

## Working Memory (Within a Single Task)

For multi-step tasks, give the agent an explicit scratchpad separate from the
user-facing output: a place to jot intermediate results, partial reasoning, or extracted
facts before producing the final answer. Two concrete forms: a literal "whiteboard" the
agent writes to and reads from across steps, or inline note-taking (margin-note-style
annotations on input before answering) — both measurably help on tasks that require
tracking several pieces of information across multiple steps.

## Memory Management — What to Keep, What to Drop

Memory isn't unbounded; managing it is two operations: deciding what to add, and deciding
what to evict when space runs out.

- **FIFO eviction**: simplest, but risks dropping something critical (like the original
  task goal) purely because it's old.
- **Summarization + entity tracking**: compress older turns into a running summary while
  keeping a separate index of named entities/facts that summarization tends to blur out.
- **Reflective merge**: after each new piece of information arrives, have the agent decide
  whether it should be added fresh, merged with something existing, or used to replace
  outdated/contradicted information — more accurate than blind FIFO or blind append, at the
  cost of an extra decision per turn.

Pick based on task length and stakes: short tasks tolerate FIFO; long-running or
high-stakes agents (the ones accumulating user preferences or critical state over many
sessions) justify the extra cost of summarization or reflective merge.
