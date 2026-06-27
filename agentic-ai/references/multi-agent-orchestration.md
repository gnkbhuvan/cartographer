# Multi-Agent Orchestration & Build-vs-Buy

## Single Agent vs. Multi-Agent

**Default to single agent.** Multi-agent systems add communication overhead, coordination
complexity, higher token cost (agents talking to each other consumes tokens too), and new
failure modes (conflicting actions, resource contention) — none of which are free.

Multi-agent earns its cost when you genuinely need:
- **Specialization**: distinct roles requiring different expertise/tools/prompts that would
  otherwise bloat one agent's instructions into an unmanageable, ambiguous mess.
- **Parallelism**: independent subtasks that can run concurrently to cut wall-clock time.
- **Fault isolation**: one agent failing shouldn't take down the whole system.
- **Scale**: the task's scope genuinely grows beyond what coordinating logic in a single
  agent can hold coherently.

**Parsimony principle**: when multi-agent is justified, add the *minimum* number of agents
that achieves it. Each additional agent is more coordination surface, not a free capability
add-on.

## Coordination Strategies

| Strategy | Mechanism | Strengths | Weaknesses | Best for |
|---|---|---|---|---|
| **Manager** | One central agent assigns tasks to subordinates | Clear task assignment, fewer communication paths | Single point of failure, scalability bottleneck | Structured, hierarchical workloads |
| **Hierarchical** | Multi-tier — higher levels oversee groups of lower-level agents | Scalable, distributed responsibility | Design complexity, latency through layers | Large, complex systems with natural sub-grouping |
| **Democratic/consensus** | All agents have equal voice, decide by consensus | No single point of failure, adaptable | High communication overhead, slow decisions | Fairness-critical or distributed-sensing tasks |
| **Actor-critic** | One agent acts, another evaluates and feeds back | Adaptive, decentralized | Needs sophisticated alignment between the two, resource-intensive | Dynamic environments needing continuous adjustment |
| **Automated design (meta-agent)** | A meta-agent generates/refines the agent system itself | Self-improving, generalizes across domains | Needs careful safety oversight — it's modifying its own architecture | Research and continuously-shifting environments, not typical production |

Pick the simplest strategy that matches your actual coordination need — manager/hierarchical
covers the large majority of real production cases; reach for democratic or actor-critic
only when the task genuinely has no natural single point of authority.

## A Different "Multi-LLM" Pattern: Cost Routing, Not Cooperation

Don't confuse cooperative multi-agent (above) with **multi-model cost optimization**, which
solves a different problem — using cheaper/smaller models where they suffice:

- **Cascades**: try a small/cheap model first; if its confidence is below a threshold,
  escalate to a bigger model; repeat up the size ladder. Needs a real confidence signal —
  encoder models can use calibrated output probabilities; decoder models need
  self-consistency (sample multiple times, check agreement) or margin sampling (gap between
  top-2 token probabilities), not the model's own stated confidence (see
  `planning-and-reasoning.md`: self-stated confidence isn't trustworthy).
- **Routers**: classify the input (intent, difficulty) up front and dispatch to exactly one
  model — cheaper than a cascade (no wasted small-model pass when it was obviously going to
  fail) but only as good as the router's classification accuracy.
- **Task-specialized models**: decompose into subtasks, send each to whichever model
  (general-purpose vs. fine-tuned/specialized) fits it best.

This pattern is usually simpler to operate correctly than cooperative multi-agent and solves
a real, common problem (cost) — consider it before reaching for a full multi-agent system
if what you actually need is "use a cheap model when the task is easy."

## Build vs. Buy

**Decision 1 — native SDK or framework**: default to the provider's native SDK (Claude
Agent SDK / OpenAI Agents SDK) for single-provider, single-agent-loop needs. Reach for a
framework (LangGraph, CrewAI, AutoGen, Swarm, MetaGPT) when you need multi-provider
portability or a graph-style orchestration topology — branching, cycles, shared state
across agents — that a hand-rolled loop would have to reinvent.

**Decision 2 — prototype vs. production framework**: frameworks like LangGraph/LangChain/
LlamaIndex are well-suited to prototyping — fast to stand up, lots of integrations. For
production, many teams either extend the open-source framework or build a thin internal
one once requirements have stabilized, trading the framework's generality for tighter
control over the specific failure modes their system actually has.

**Governing principle for both decisions**: don't complicate the architecture — more
agents, more framework abstraction, more orchestration machinery — without a specific,
named reason. The simplest setup that solves the task is correct until it demonstrably
isn't.
