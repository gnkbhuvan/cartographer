# Tools & MCP Architecture

## Tool Categories

Three kinds of tools an agent typically needs:
- **Knowledge augmentation**: retrievers, SQL executors, internal/external APIs, web search
  — gets the agent information it doesn't have natively.
- **Capability extension**: calculators, calendars, unit/timezone converters, code
  interpreters — does things the model itself does unreliably (arithmetic, exact lookups).
- **Environment action**: read tools (perceive state) and write tools (change state — send
  an email, create a ticket, execute a transaction). Write tools are where irreversibility
  risk concentrates — see `failure-modes-and-safety.md` for gating.

## Designing and Curating the Tool Set

- Write clear, disjoint tool descriptions — overlap or ambiguity between two tools'
  descriptions is the single biggest driver of wrong tool selection, more so than tool
  count alone.
- Don't add tools speculatively. Run an ablation: remove a tool and check whether task
  performance actually drops. Tools the agent rarely or never uses correctly are candidates
  for removal, better prompting, or replacement.
- Monitor tool-use distribution and tool-transition patterns in production — tools that are
  frequently invoked back-to-back are candidates for merging into one combined tool, which
  reduces selection surface.
- A larger, well-curated tool set genuinely can outperform a smaller one or a bigger model
  alone — the goal isn't "fewer tools at all costs," it's "no tool whose presence isn't
  earning its keep."

## MCP (Model Context Protocol) Architecture

MCP exists to solve an M×N integration problem: without a shared protocol, connecting M
LLM clients to N tools/data sources means M×N custom integrations. MCP standardizes the
interface so it becomes M+N.

| Component | Role |
|---|---|
| **Host application** | Whatever hosts the client(s) and talks to the LLM — a chatbot, an IDE, a custom app. Minimal required scope: talk to an LLM, host one or more MCP clients. |
| **MCP client** | The interface between host, LLM, and server. Discovers a server's tools/resources/prompts, translates them into the target LLM's tool-call format, and routes calls. One client-to-server connection is one-to-one; use multiple client instances (or a session-group abstraction) to talk to multiple servers at once. |
| **MCP server** | Exposes the actual primitives: tools, resources, prompts, and (for advanced use) the ability to request a sampling call back to the host's LLM. |
| **Transport** | Carries messages between client and server. **stdio**: local subprocess, simplest, used when the server runs alongside the host. **Streamable HTTP**: remote servers — must be secured with authentication and origin validation, since it crosses a network boundary. |

**Architecture decisions this implies**:
- Keep the host application's own logic separate from MCP connectivity logic — the host
  only needs to talk to an LLM and manage client connections, nothing more.
- Choose stdio by default for anything colocated; reach for Streamable HTTP only when the
  server genuinely needs to be remote, and treat that as a security boundary requiring auth.
- Wrap raw MCP tool/resource objects in an internal abstraction layer that translates them
  to your target model's tool-call format — this is what keeps the agent model-agnostic if
  you ever swap providers.
- If a server can request something back from the host's LLM (the "sampling" capability),
  that's a real security boundary: an external server gaining the ability to spend calls
  against an LLM you're paying for needs a human-in-the-loop approval gate before that
  request is honored, not implicit trust.

## Tool Integration Pattern (Provider-Agnostic Shape)

Regardless of which native SDK or framework executes it, the shape is always: (1) make the
model aware of available tools (names + concise descriptions in the system context), (2)
let the model select and emit a structured call, (3) execute the call in your application
code and return the result as the next turn's input. The actual prompt-level template for
this (ReAct-style Thought/Action/Observation, tool-call JSON schemas) lives in the
`prompt-engineering` skill — this is the architecture above that template, not a
replacement for it.
