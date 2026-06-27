# Planning & Reasoning

## Decouple Planning from Execution

The single most load-bearing architectural pattern for reliable agents: generate a plan,
**validate it**, and only then execute — don't let the model start acting on its first
draft plan. Validation can be a cheap heuristic (reject plans over N steps, reject invalid
actions outright) or a separate AI judge asking "is this plan reasonable, and can it be
improved?" This effectively makes planner, validator, and executor three distinct roles,
even if the same model plays more than one of them.

**Why this matters**: an unvalidated agent can commit to a thousand-step plan that wastes
time and money before anyone notices it was never going to work. Validation is the cheapest
point to catch that.

## Plan Generation Approaches

- **Prompted with examples**: few-shot plan exemplars in the prompt (see `prompt-engineering`).
- **Hierarchical planning**: generate a coarse high-level plan first, then expand each step
  into detail only when it's about to execute — avoids over-committing to low-level details
  that may not survive contact with the first few steps' actual results.
- **Natural-language steps vs. function-name steps**: plans expressed in natural language
  ("get the current date, then retrieve top products") are more robust to underlying API
  changes than plans that hard-code function names directly; translate to calls at
  execution time instead of planning time.
- **Stronger models plan better.** If planning quality is the bottleneck, the model
  upgrade lever is more reliable than prompt tweaking alone — but check cost/latency
  trade-offs before defaulting to the largest available model for every step (see
  multi-agent routing in `multi-agent-orchestration.md` for using cheaper models on easier
  subtasks).

## Control Flow Beyond Sequential

Plans aren't always a straight line. Recognize and design for: **parallel** steps that
don't depend on each other, **conditional** branches (if/then based on an observation), and
**loops** (repeat until a condition holds). Non-sequential control flow is harder for a
model to both generate and translate into execution correctly — budget extra planning and
validation effort specifically for these, don't treat them as a free upgrade over a
sequential plan.

## Reasoning Patterns and Their Honest Limitations

- **ReAct** (interleaved Thought → Action → Observation, looping until done): the most
  common agentic reasoning pattern. Despite its popularity, it's been shown to be brittle —
  don't treat it as a solved default; validate it against your own task rather than
  assuming it transfers.
- **Reflexion** (the agent reviews its own output against a failure signal and retries with
  that feedback): genuinely useful when there's a clear failure signal to react to (failing
  tests, a validator's rejection) — but its effectiveness is often overstated, and invoking
  it too often can cause a model to second-guess correct solutions rather than fix wrong
  ones. Trigger it on a concrete signal (e.g., "stuck repeating the same action 3+ times"),
  not unconditionally after every step.
- **Self-stated confidence is not a reliable signal.** Asking a model to state how
  confident it is in its own output has not been shown to be trustworthy — don't build a
  control-flow branch (e.g., "only escalate to a human if confidence < X") on a number the
  model invented about itself.

## Reflection Timing

If using a reflection/self-critique step at all, place it deliberately rather than after
every single action: candidates are right after the user's request (a feasibility check
before committing to a plan), right after plan generation (before execution starts), after
each step (expensive — only for high-stakes steps), or once at the end (cheapest, catches
only end-state problems). Match the placement to what the step actually risks getting
wrong, and to the latency/cost budget — every reflection pass is another model call with
its own (imperfect) signal-to-noise ratio.
