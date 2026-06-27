# Agent Fundamentals

## What Makes Something an Agent

An agent perceives its environment and acts on it, in a loop: perceive the current state →
reason about the task and plan → act (often via a tool) → observe the result → decide
whether the goal is met or another loop is needed. The defining trait is **autonomy**: the
sequence of actions isn't specified in advance — the model itself decides what to do next
based on what it just observed.

## Agent vs. Workflow vs. Plain Prompt

| | Plain prompt | Workflow | Agent |
|---|---|---|---|
| **Who decides the steps** | N/A — one shot | Code (deterministic) | The model, dynamically |
| **Sequence known in advance** | Trivially, yes | Yes | No |
| **Right for** | Single well-defined transformation | Known, repeatable multi-step process | Tasks where the right next step depends on what was just observed |

Named workflow patterns worth recognizing as the *non-agentic* alternative before reaching
for an agent: prompt chaining (A's output feeds B), parallelization (multiple calls at
once, combined), routing (classify input, dispatch to one of several fixed paths),
orchestrator-worker (one call decomposes, several workers execute, one call assembles),
evaluator-optimizer (generate, then a second pass critiques and refines). If one of these
fixed shapes solves the task, it's a workflow — building it as an agent adds autonomy
nobody asked for, and with it the reliability and tool-selection costs in `SKILL.md`'s
first-principles section.

## When Agents Are Actually Warranted

Agents earn their complexity on tasks that involve: summarizing/synthesizing large,
varied information; operating over unstructured input where the right response depends on
context; reasoning over content (text/images) rather than executing a fixed lookup; or
genuine multi-step problems where the next step depends on what the previous step
returned (can't be pre-wired as a workflow).

Agents are a poor fit for: single well-defined lookups (use a plain prompt or a tool call
directly), tasks with a known fixed sequence (use a workflow — it's more debuggable and
cheaper), and — as of current capability — mission-critical/irreversible actions without a
human gate (current agents get stuck in loops, take incorrect actions, and can't reliably
self-correct; treat autonomy as something to earn via evaluation, not assume).

## The Core Loop, Concretely

A task has a **goal** and **constraints** (e.g., "plan a two-week trip, budget $5,000").
The agent: decomposes the goal into subtasks, selects tools/knowledge for each, executes
(synchronously or asynchronously), and synthesizes a final answer in the requested format.
Not all decompositions are equally good — order matters (e.g., filter by the cheapest
criterion first to shrink the search space before applying expensive filters), so plan
quality is itself something to design and evaluate, not assume.

## A Note on Honesty About Capability

Treat current-generation autonomous agents as genuinely capable but not yet reliable enough
to deploy unsupervised on consequential tasks. The honest framing to give a user: agents
are good at extending what's possible (multi-step, tool-using tasks a single prompt can't
do), but they fail differently than a single bad prompt does — they loop, they take wrong
actions confidently, and they don't reliably notice their own mistakes. Design for that
reality (see `failure-modes-and-safety.md`) rather than assuming capability improves the
failure mode away.
