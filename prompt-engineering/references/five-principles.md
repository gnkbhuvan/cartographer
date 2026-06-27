# Five Principles of Prompting (Expanded)

---

## Principle 1: Give Direction

Describe the desired style, persona, or reference a relevant expert.

**Forms of direction**:
- **Role prompting**: "You are a senior software engineer reviewing code..."
- **Persona emulation**: "In the style of Steve Jobs..." — models know famous figures from training data.
- **Self-generated direction (prewarming)**: Ask the model for best practices on the task first, then ask it to follow its own advice within the same conversation window. This is sometimes called internal retrieval.
- **External rules/guidelines**: Insert industry best practices, brand guidelines, or domain rules as context. Increases token cost but may significantly improve quality.
- **Descriptive keywords**: "concise," "technical," "enthusiastic," "actionable," "for beginners."

**Trade-off**: Too much direction narrows creativity; too little produces average outputs. Err on the side of more direction.

**Image direction**: Artist names (Van Gogh, Miyazaki), art styles (cyberpunk, art deco), camera specs (Panasonic DC-GH5), composition elements (glass-top table, campfire outdoors).

---

## Principle 2: Specify Format

Define what rules to follow and the required structure of the response.

**Specify BOTH what to include AND what to exclude**:
- "Return a comma-separated list. No numbered items."
- "Respond with only the code, no explanation."
- "Only return valid JSON. Never include backtick symbols."

**For production**: Always use a parseable format (JSON/YAML). Validate on every response. Retry on parse failure.

**Format vs. style distinction**: Format = structure (JSON, bullet list, stock photo). Style = aesthetic/tone (Steve Jobs style, Van Gogh painting). When they clash, drop whichever is less important.

**Image format modifiers**: stock photo, oil painting, illustration, 3D render, screenshot, in Minecraft, pencil sketch, watercolor, claymation, charcoal, blueprint, isometric, line art.

---

## Principle 3: Provide Examples

Insert a diverse set of test cases where the task was done correctly.

| Shots | Behavior |
|-------|----------|
| Zero-shot | Works but inconsistent. Sign of a powerful model. |
| One-shot | Substantial improvement in reliability. |
| Few-shot (2-5) | Sweet spot for most tasks. |
| Many-shot (>5) | Reliability increases, creativity decreases. Overfitting risk. |

**Diversity is essential**: Similar examples produce outputs overfitted to that narrow pattern. Include edge cases.

**Format in examples must match desired output exactly**. The model mimics the pattern it sees.

**When examples are hard to create**, try Give Direction first instead—it's often easier than collecting good examples.

**Dynamic example selection**: For RAG systems, embed the user input and retrieve the most semantically similar examples from a vector store at runtime.

---

## Principle 4: Evaluate Quality

Identify errors and rate responses. Test what drives performance.

**Ladder of rigor** (start simple):
1. Blind prompting (eyeball one result)
2. Multiple runs with thumbs-up/down (5-10 trials)
3. Blind A/B comparison between prompt variants
4. Elo rating system (side-by-side, like Chatbot Arena)
5. Programmatic evaluation against ground truth
6. GPT-4 as evaluator (stronger model judges weaker model)

**Evaluation dimensions**: accuracy, format compliance, hallucination rate, consistency, token cost, latency, safety, adversarial robustness, similarity to reference (BLEU, ROUGE, embedding distance).

---

## Principle 5: Divide Labor

Split tasks into multiple steps, chained together for complex goals.

**Decomposition patterns**:
- **Sequential chaining**: Output of A becomes input of B.
- **Parallel + combine**: Generate multiple outputs, rate and select best.
- **Self-evaluation**: Step 1 generates, Step 2 evaluates/critiques.
- **Meta-prompting**: LLM generates prompt for another LLM or image model.
- **Progressive summarization**: Chunk → summarize each → summarize summaries.

**Why division works**: LLMs predict tokens sequentially—they can't know the overall output while generating it. Self-evaluation (reviewing completed output) is significantly more accurate than in-line correction.

**Prompt chaining libraries**: LangChain (Python/JS) provides tooling for chaining templates, managing state, and observing multi-step workflows.

---

## Image Generation Notes (Midjourney / Stable Diffusion / DALL-E)

Beyond direction (artist/style) and format modifiers covered above:

- **Negative prompts**: state what to exclude ("no blur, no low quality, no distortion")—separate from describing what you want.
- **Weighted terms**: emphasize key elements, e.g. Midjourney's `::weight` syntax, when one part of the prompt matters more than the rest.
- **img2img**: supply a base image URL as the starting point instead of generating from text alone.
- **Permutation prompting**: systematically test combinations of format × style × composition rather than guessing one combo at a time—this is "Provide Examples" and "Evaluate Quality" applied to image prompting.
- **Meta-prompting for images**: use an LLM to turn a plain product/scene description into a well-formed Midjourney/DALL-E prompt—works because LLMs are themselves competent prompt engineers.
