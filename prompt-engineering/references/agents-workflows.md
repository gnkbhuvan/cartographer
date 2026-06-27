# Agents, Workflows & Tool Usage

---

## Temperature & Sampling

### Temperature Selection

| Temperature | Behavior | When to Use |
|------------|----------|-------------|
| 0 | Nearly deterministic; always picks most likely token | Correctness critical: code gen, classification, extraction |
| 0.1–0.4 | Mostly consistent, slight variation | General tasks with small diversity needed |
| 0.5–0.7 | Noticeable randomness; creative | Brainstorming, creative writing, exploring alternatives |
| 1.0 | Mirrors training distribution | Statistical sampling |
| >1.0 | "Drunk" model; errors compound | Avoid in production |

**Fundamental trade-off**: Higher temp = more alternatives but lower correctness. Lower temp = more consistent but can get stuck in repetition loops.

### Logprobs

- `logprobs`: Returns log probability of each generated token. Closer to 0 = higher confidence.
- `top_logprobs`: Returns top N alternative tokens and probabilities. Use to understand what else the model considered and identify uncertainty.
- **Confidence estimation**: Low logprobs suggest the model is uncertain—flag for human review.

### Other Parameters

- **top_p (nucleus sampling)**: Alternative to temperature. 0.9 for diverse, 0.1 for focused.
- **stop sequences**: End generation at pattern match. E.g., `["\n\n", "###"]` to prevent rambling.
- **n (parallel completions)**: Generate multiple variations in one API call. n=5-10 for evaluating consistency.

---

## Tool Usage Guidelines

**Tool definitions should be**:
- Named clearly and uniquely (avoid name collisions).
- Parameter types and descriptions are precise.
- Include example usage in the description.
- Keep total tool count small (<10; models get confused with too many options).
- Include error handling guidance: "If the tool returns an error, try adjusting parameters."

**Tool call flow**: Model outputs a tool call → Application executes it → Result is fed back as the next prompt turn → Model outputs next step or final answer.

**Tool safety—gate at the application layer, not the prompt**: don't just write "double-check
with the user before doing X" in a tool's description and call the risk solved. Models are
inherently undependable at honoring soft instructions for irreversible/dangerous actions
(deletions, payments, sending messages). Let the model emit the request, then have the
*application code* intercept every such call and require explicit human sign-off before the
real side-effecting API runs.

**OpenAI Functions vs. ReAct**: Functions are simpler (single-turn tool use). ReAct is more flexible (multi-turn reasoning + action loops). ReAct handles complex sequences better; Functions work well for single-step lookups or calculations.

---

## ReAct Agent Pattern

```
You are an agent that can use tools.

Available tools:
- search(query: str): Search for information.
- calculate(expression: str): Evaluate math expression.

Use this format:
Thought: [reasoning about what to do next]
Action: tool_name(tool_input)
Observation: [result]
... (repeat as needed) ...
Thought: I now have enough information.
Final Answer: [response to user]

User question: {question}
```

---

## Workflow Design

### When to Use Workflows vs. Agents

**Use workflows** when:
- Task has a predictable structure.
- Multiple independent subtasks exist (parallelizable).
- Same task runs repeatedly with different inputs.
- Deterministic business logic between LLM calls.

**Use conversational agents** when:
- Task is interactive (back-and-forth with user).
- Task requires exploration and adaptation.
- Each step depends on the previous result.

**Signal it's time to decompose a struggling agent into a workflow**: the system prompt has
grown large and confusing, there's no natural way to queue/track units of work, or there's no
clear story for recovering from a failed step. When you see these, stop patching the single
agent and split into explicit tasks instead.

**Escalation ladder for a struggling single-prompt/single-agent task** (cheapest fix first):
1. Add chain-of-thought ("let's think step by step") before reaching for tools or more agents.
2. If the model calls tools prematurely, suppress tool use for one turn to force a planning
   pass first (e.g. `tool_choice="none"`), then allow tools.
3. Apply Reflexion: let the model review its own output against a failure signal (failing
   tests, a validator) and retry with that feedback injected—only viable when the domain
   allows do-overs (not for irreversible actions).
4. Fall back to a full multi-agent setup (planner/executor/critic, AutoGen-style) only as the
   last and most expensive resort, once 1-3 have been tried and failed.

### Workflow Patterns

- **Sequential chain**: A → B → C (each depends on previous).
- **Parallel fan-out**: A → [B, C, D] simultaneously → combine.
- **Conditional branching**: A → if X then B else C.
- **Map-Reduce**: Split input → process chunks in parallel → combine.

### Workflow Assembly Rules

1. **Define the DAG**: Which tasks depend on which?
2. **Design each prompt independently**: Each does ONE thing well.
3. **Handle errors between steps**: Validate input, provide fallbacks.
4. **Pass structured data**: JSON between steps, not free text.
5. **Log intermediate results**: Essential for debugging failures.

### Agent Memory Types

- **ConversationBufferMemory**: Stores full conversation. Simple but unbounded growth.
- **ConversationBufferWindowMemory**: Keeps last K turns only.
- **ConversationSummaryMemory**: Summarizes conversation as it grows.
- **ConversationSummaryBufferMemory**: Buffer of recent turns + summary of older turns.
- **ConversationTokenBufferMemory**: Truncates to fit within token limit.

### Advanced Agent Patterns

- **Plan-and-Execute**: Generate complete plan first, execute each step, adjust as needed.
- **Tree of Thoughts**: Branch reasoning paths, evaluate each, select best, backtrack if needed.
- **Roles and Delegation**: Assign Planner, Executor, Critic, and Synthesizer roles to separate LLM calls.
