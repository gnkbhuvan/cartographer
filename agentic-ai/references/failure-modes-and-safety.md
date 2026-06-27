# Failure Modes, Evaluation & Safety

## Failure Taxonomy

Name the failure before trying to fix it — these are distinct problems with distinct fixes:

| Failure | What it looks like | Where it comes from |
|---|---|---|
| **Tool-use failure** | Wrong tool selected; right tool, wrong parameters; right tool and parameters, wrong values | Ambiguous tool descriptions, too many overlapping tools, or unclear parameter constraints |
| **Goal failure** | The plan executes successfully but doesn't actually solve the task, or silently violates a stated constraint (budget, deadline) | Plan generation didn't fully encode the constraints, or validation didn't check for them |
| **Reflection failure** | The agent believes it completed the task when it didn't (e.g., assigned 40 of 50 required items but reports done) | Self-assessment without an external check — see "never let a model verify its own work alone" in `SKILL.md` |
| **Time/budget violation** | Task technically completes, but after the deadline or over budget | No explicit constraint tracking during execution, only at the end |
| **Loop/stuck state** | Repeats the same action without making progress | No loop-detection or step-count ceiling |

## Evaluation Metrics

Track these explicitly rather than relying on spot-checking outputs:
- **% of generated plans that are valid** (pass your validator before execution)
- **Average plans needed to reach one valid plan** (a proxy for how much planning is
  actually costing you in retries)
- **% of valid tool calls** vs. invalid-tool / invalid-parameter / wrong-value-rates,
  broken out separately — they have different fixes
- **Average steps to complete** and **average cost per task** — efficiency, not just
  correctness
- **Task completion rate** and **user satisfaction** (explicit signals like thumbs up/down,
  or implicit signals from logs — repeated rephrasing, abandonment, escalation to a human)

Combine functional testing (correctness on known cases, boundary/edge-case handling) with
generalization testing (does it hold up on inputs unlike anything in your test set) — an
agent that only works on cases resembling its examples hasn't actually generalized.

## Human-in-the-Loop & Safety Gating

**Gate at the application layer, not the prompt.** A tool description that says "confirm
with the user before doing X" is not a safety control — models don't reliably honor soft
instructions for irreversible actions. The application code, not the model, must intercept
any call to a consequential tool (payments, deletions, messages sent on someone's behalf,
or a server requesting LLM calls on your account) and require explicit sign-off before the
real side-effecting action runs. (Cross-reference: this is the same principle as
`prompt-engineering`'s tool-safety guidance — apply it here at the system-design level, not
just the prompt level.)

**Communicate uncertainty honestly, don't hide it**: surface confidence visibly (not via the
model's self-reported number — see `planning-and-reasoning.md`) so a user can calibrate
trust. Frame agent outputs as suggestions to verify when stakes are non-trivial, not as
final verdicts to rubber-stamp.

**Prevent automation bias**: the risk isn't just the agent being wrong — it's users
trusting it anyway. Make low-confidence outputs visibly different from high-confidence
ones, invite verification before approval on anything consequential, and don't design the
UX so that "accept" is the path of least resistance for actions that matter.

**Ask for guidance instead of guessing on genuine ambiguity**: when the agent hits a
fork it can't resolve from context, a focused clarifying question beats a confident wrong
assumption — but don't over-ask either; reference what's already known rather than
re-asking, and don't interrupt for low-stakes ambiguity.

## Graceful Failure

When the agent does fail: acknowledge it plainly rather than producing a confident wrong
answer, preserve enough state that the task can resume once the issue is fixed rather than
starting over, and log the failure with enough detail to fix the underlying cause — not just
to retry and hope. A system that fails the same way repeatedly without that feedback loop
will keep failing that way.
