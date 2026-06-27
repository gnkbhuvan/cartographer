# LLM Architecture Essentials for Prompt Engineers

---

## What LLMs Are

- **Document completion engines**: Prompt = prefix of a document; Completion = statistically most likely continuation of that document.
- **Training data mimics**: Models mimic patterns found in training data. Ask: "How would a document starting like this most likely continue?" NOT "How would a reasonable person respond?"
- **Auto-regressive**: One token at a time. No pausing, no backtracking, no editing. Once a token is emitted, the model is committed to it.
- **Single-pass, left-to-right**: The model reads the prompt once, processing each token in order. Information flows only leftward (earlier tokens) and upward (lower layers). There is no "looking back."

## Tokenization

- **~4 characters per token** for English natural language. Less for special chars, numbers, and non-English languages.
- **Deterministic tokenizers**: The same text always produces the same tokens. Typos create dramatically different token sequences.
- **Capitals are different tokens**: "For" and "for" are different tokens. Avoid case-transformation tasks.
- **Subtoken tasks are hard**: Letter counting, reversal, anagrams—these require breaking tokens apart, which LLMs do poorly. Delegate to pre/post-processing code.
- **Vocabularies have special tokens**: end-of-text, ChatML delimiters (`<|im_start|>`, `<|im_end|>`). These are reserved and users can't inject them via the API.

## The Little Red Riding Hood Principle

"Don't stray far from the path upon which the model was trained"—the
single most load-bearing rule for prompt design. Mental model: pick a random document from
the training set; all you know is it starts with your prompt; what's the statistically most
likely continuation? That's the output to expect. Consequences:

- Make prompts look like real documents the model has plausibly seen—markdown reports, code
  files, chat transcripts, structured docs—not artificial templates that resemble nothing.
- For **fine-tuned** models the rule splits in two: (1) make the prompt look like the start of
  one of the documents you fine-tuned on, and (2) make sure it does *not* look like one of the
  base model's original pre-training documents, or the fine-tuning will be bypassed.

## Repetition Trap

Auto-regressive models can fall into repeating patterns they can't escape. At temperature=0, if continuing a list is more likely than stopping, the list never ends. Mitigations: increase temperature, use stop sequences, detect and filter repetition in code.

## Hallucinations & Truth Bias

- **Truth bias**: The model assumes its prompt is true and won't correct false premises. Giving it a counterfactual prompt produces counterfactual completions. You are responsible for prompt correctness.
- **Make-believe prompts**: Instead of "Pretend X happened," write "It's 2031, a year since X happened." The model will complete naturally from this premise.
- **"Don't make stuff up" is useless**: The model doesn't distinguish fact from fiction—both are just token predictions. Structure output for verifiability instead.

## Chat Models & RLHF

**Training pipeline**:
```
Base Model (raw text completion, ~500B tokens)
  → SFT Model (13k handcrafted assistant conversations)
    → Reward Model (33k human-ranked completions)
      → RLHF Model (PPO optimization, ~31k prompts)
```

**Key effects of RLHF**:
- Aligns models to be Helpful, Honest, Harmless (HHH).
- Teaches honesty: models learn to express uncertainty rather than fabricate when unsure. SFT alone cannot teach this—it requires the reward model's introspection.
- **Alignment tax**: RLHF can reduce raw capabilities. Mitigated by mixing original pre-training data.

**ChatML roles**: `system` (sets behavior, followed most strictly), `user` (real input), `assistant` (model output). Never put user-generated content in a system message—this bypasses injection protections.

**Completion vs. Chat API**: Chat models can be chattier and add commentary. For tasks needing pure output (code, structured data), consider the completion API or strict format instructions.

## Fine-Tuning vs. Prompting — Decision Tree

Ask in order:
1. **Is the task adequately solved by prompting on a current model?** If yes, stop—don't fine-tune.
2. **Is the task stable** (won't change shape every few weeks)? If no, keep prompting; fine-tuning on a moving target is wasted effort.
3. **How many good examples can you produce?** Hundreds-thousands → LoRA. Tens of
   thousands+ → full fine-tuning becomes economical (fine-tuning starts to beat prompt
   engineering once you can supply a few thousand examples).
4. **What depth of change is needed?** Style/format/tone/expectations on top of existing
   knowledge → **LoRA** (trains a small low-rank diff matrix; hours-days). Genuinely new
   domain knowledge the base model lacks → **full fine-tuning** (weeks-months); LoRA can't
   teach what the base model never learned.

**Loss masking**: when fine-tuning, restrict training loss to the answer portion of each
example, not the prompt/problem portion—you don't need the model to learn to generate the
prompt itself.

**Soft prompting**: an alternative to hand-crafting prompt wording—use ML to find an optimal
internal "state of mind" vector directly from example outputs. Framework-dependent, not
universally available; treat as a fallback when manual prompt wording plateaus and full
fine-tuning is overkill.
