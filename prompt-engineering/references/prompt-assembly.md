# Prompt Assembly & Structure

---

## Anatomy of the Ideal Prompt

```
┌───────────────────────────────────────────────┐
│ System message / Role definition               │  ← Who is the assistant?
├───────────────────────────────────────────────┤
│ Static Content                                 │
│   • Task instructions                          │  ← What to do?
│   • Few-shot examples                          │  ← What does good look like?
│   • Constraints and rules                      │  ← What to avoid?
├───────────────────────────────────────────────┤
│ Dynamic Content                                │
│   • Retrieved context (RAG)                    │  ← What facts are relevant?
│   • User input                                 │  ← The data to process
│   • Conversation history                       │  ← What was said before?
├───────────────────────────────────────────────┤
│ Output indicator                               │  ← "Answer:", "```json", etc.
└───────────────────────────────────────────────┘
```

## Content Ordering Rules

Information placement matters because the model reads once, left-to-right:

1. **Position**: Earlier content influences tone/direction more. Later content influences specific outputs more. Few-shot examples should be immediately before the target input.
2. **Importance**: Essential context must be prominent. Non-essential context competes for attention—trim it aggressively.
3. **Dependency**: If section B depends on section A, A must come first. Instructions referencing "the document below" must appear above the document.

**Lost in the middle / "Valley of Meh"**: content in the exact middle of long contexts is least well-attended—worse than either the start (primacy) or the end (recency/in-context-learning effect). Don't place anything critical there.

**Sandwich technique**: the direct mitigation. State the actual goal/question once in the introduction AND once again immediately before the model must answer (a "refocus" line). The two restatements bracket the Valley of Meh so the model never has to act on something it half-forgot.

## Document Types and Structures

| Type | Example tasks | Structure |
|------|--------------|-----------|
| **Advice conversation** | Q&A, support, tutoring | System role → Question → Context → Answer format |
| **Analytic report** | Summaries, analysis, reviews | Task → Context → Analysis steps → Report format |
| **Structured document** | JSON extraction, classification | Schema → Examples → Input → Output indicator |
| **Code generation** | Function writing, refactoring | Language/framework → Spec → Constraints → Output |

For **analytic reports**, give the completion a table-of-contents-style "scratchpad" section up front (acts as a CoT space) and a trailing "Appendix" heading—useful as a `stop` sequence to cut generation short once the real content is done.

## Content Sources

**Static** (fixed per template): instructions, formatting rules, few-shot examples.

**Dynamic** (varies per request): user input, RAG-retrieved context, conversation history, tool outputs, database query results, external API data.

## Ranking Content by Utility

When the context window is limited, prioritize:

| Tier | Description | Examples |
|------|-------------|----------|
| **Critical** | Cannot complete without it | Instructions, user input |
| **Important** | Significantly improves quality | Examples, key facts |
| **Helpful** | Nice to have | Background context, style notes |
| **Superfluous** | Doesn't help, may distract | Remove from prompt |

## Formatting Snippets

- Use **consistent delimiters** across all sections: `### Examples`, `---`, or section labels.
- **Label all sections clearly**: `Task:`, `Context:`, `Examples:`, `Input:`, `Output:`.
- Use **triple backticks for code**, JSON, YAML blocks.
- **No ambiguity** between instructions and input data—use clear section boundaries.
- For few-shot examples, keep **identical formatting** across every example.

## Context Window Management

- **Count tokens** with tiktoken (OpenAI) or equivalent tokenizer.
- **Prompt + expected completion must fit** within the context window.
- For long conversations: keep last N turns verbatim + summarize earlier turns.
- For long documents: split into chunks, summarize each, then summarize summaries.
- **Aggressively remove superfluous content**—excess context degrades outputs (lost in the middle problem).
