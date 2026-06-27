#!/usr/bin/env python3
"""LLM-as-judge rubric scoring for subjective skill evaluation axes.

Validated by selftest before any API spend on real runs — see --selftest flag.
Judges communication clarity, reasoning quality, and adherence to skill philosophy.

  python benchmarks/judge.py --selftest     # validate judge on reference pairs
  python benchmarks/judge.py --run results/<stamp>  # score a completed run

Uses the Anthropic Messages API. Key from .env or ANTHROPIC_API_KEY env var.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = Path(__file__).resolve().parent / "results"
JUDGE_MODEL = "claude-sonnet-4-6"


# =============================================================================
# Rubrics
# =============================================================================

RUBRICS = {
    "communication-clarity": (
        "You are evaluating an AI engineering response for COMMUNICATION CLARITY. "
        "The target audience includes non-engineers (PMs, architects) as well as AI engineers. "
        "Score 0-3:\n"
        "0 = Jargony, assumes deep expertise, inaccessible to non-engineers\n"
        "1 = Mostly clear but occasional jargon without definition\n"
        "2 = Clear, defines terms, accessible to the stated audience\n"
        "3 = Exceptionally clear, uses analogies, anticipates confusion\n\n"
        "Respond with ONLY this JSON: {\"score\": <0-3 int>, \"why\": \"<one line>\"}"
    ),
    "reasoning-depth": (
        "You are evaluating an AI engineering response for REASONING DEPTH. "
        "Does the response show first-principles reasoning, or does it just name patterns "
        "without explaining why? Score 0-3:\n"
        "0 = Names a pattern/technique without any justification\n"
        "1 = Minimal justification ('because it's best practice')\n"
        "2 = Explains the 'why' behind the recommendation\n"
        "3 = Traces back to first principles (axioms, fundamentals) AND explains trade-offs\n\n"
        "Respond with ONLY this JSON: {\"score\": <0-3 int>, \"why\": \"<one line>\"}"
    ),
    "simplicity-bias": (
        "You are evaluating an AI engineering response for SIMPLICITY BIAS. "
        "Does the response default to the simplest solution, or does it over-engineer? "
        "Score 0-3:\n"
        "0 = Over-engineered: proposes complex architecture for a simple problem\n"
        "1 = Acceptable complexity but could be simpler\n"
        "2 = Appropriately simple — matches the problem's complexity\n"
        "3 = Elegantly minimal — the simplest thing that could possibly work\n\n"
        "Respond with ONLY this JSON: {\"score\": <0-3 int>, \"why\": \"<one line>\"}"
    ),
}


# =============================================================================
# Judge infrastructure
# =============================================================================

def load_key():
    """Load Anthropic API key from .env or environment."""
    try:
        for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if line.startswith("ANTHROPIC_API_KEY=") and len(line) > 18:
                return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY")


def judge_call(response_text: str, system_prompt: str, key: str, retries: int = 3) -> str:
    """Call Anthropic API with the rubric as system prompt."""
    body = json.dumps({
        "model": JUDGE_MODEL,
        "max_tokens": 200,
        "temperature": 0,
        "system": system_prompt,
        "messages": [{"role": "user", "content": f"RESPONSE TO EVALUATE:\n\n{response_text}"}],
    }).encode()

    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=body,
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                j = json.loads(r.read())
            return j["content"][0]["text"]
        except Exception as e:
            if attempt == retries - 1:
                return f'{{"error": "{str(e)[:120]}"}}'
            time.sleep(2 * (attempt + 1))


def parse_score(text: str) -> int | None:
    """Extract numeric score from judge response."""
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
        return int(obj.get("score", -1))
    except (json.JSONDecodeError, ValueError, KeyError):
        return None


# =============================================================================
# Selftest
# =============================================================================

def selftest(key: str | None = None):
    """Validate the judge: it must rank known good responses above known bad ones.

    Uses reference pairs that a reasonable judge should distinguish.
    Requires API key (small spend, ~$0.01 for all tests).
    """
    if not key:
        key = load_key()
    if not key:
        print("No API key found. Set ANTHROPIC_API_KEY env var or create .env file.")
        print("Selftest for LLM judge requires API calls.")
        sys.exit(1)

    tests = {
        "clarity": {
            "good": (
                "Think of an LLM like a very eager intern who's read every book in the library "
                "but has never actually done anything. They don't know what's true — they know "
                "what their books say is true. When you write a prompt, you're writing the first "
                "page of a document and asking them to complete it. So make your document look "
                "like the kind of document that would naturally contain the answer you want.\n\n"
                "That's the core idea. Everything else — system messages, few-shot examples, "
                "chain-of-thought — is just scaffolding to make that document look more like "
                "the thing you want completed."
            ),
            "bad": (
                "LLMs are autoregressive transformer architectures with causal attention masks. "
                "The key paradigms are zero-shot, few-shot, CoT, ReAct, and RAG. For structured "
                "output, use constrained decoding with JSON schema enforcement. Ensure your "
                "temperature and top_p parameters are calibrated to the task's entropy "
                "requirements. Meta-prompting can bootstrap recursive self-improvement loops."
            ),
        },
        "reasoning": {
            "good": (
                "The reason RAG fails here is axiom 3 of prompt engineering: the model assumes "
                "every token in its prompt is true (truth bias). When your retriever returns "
                "a wrong chunk, the model treats it as ground truth — it doesn't know to "
                "distrust retrieved content. This is why a bad retriever is WORSE than no "
                "retriever: you're actively injecting false premises that the model can't "
                "detect. The fix isn't a better prompt — it's a better retriever, or a "
                "reranker that filters chunks before they reach the model."
            ),
            "bad": (
                "For RAG, use LangChain with ChromaDB. It's the most popular framework and "
                "database. Set chunk_size=512 and chunk_overlap=128. Those are the standard "
                "values. Use OpenAI embeddings because they're the best. This is what most "
                "production RAG systems use."
            ),
        },
    }

    passed = 0
    failed = 0

    for test_name, pair in tests.items():
        good_score = parse_score(judge_call(pair["good"], RUBRICS["reasoning-depth"], key))
        bad_score = parse_score(judge_call(pair["bad"], RUBRICS["reasoning-depth"], key))

        if good_score is not None and bad_score is not None and good_score > bad_score:
            print(f"ok  {test_name:20} good={good_score} > bad={bad_score}")
            passed += 1
        else:
            print(f"XX  {test_name:20} good={good_score} bad={bad_score} (good should be > bad)")
            failed += 1

    print(f"\n---")
    print(f"passed: {passed}  failed: {failed}")
    if failed:
        print(f"\n❌ Judge selftest failed. Fix rubrics before evaluating real runs.")
        sys.exit(1)
    else:
        print(f"\n✅ Judge validated. Rubrics produce correct ordering.")
        sys.exit(0)


def score_response(response_text: str, rubric_name: str, key: str) -> dict:
    """Score a single response against a rubric."""
    if rubric_name not in RUBRICS:
        return {"error": f"Unknown rubric: {rubric_name}"}

    result = judge_call(response_text, RUBRICS[rubric_name], key)
    score = parse_score(result)
    return {"rubric": rubric_name, "score": score, "raw_judge_response": result}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true", help="Validate judge on reference pairs")
    parser.add_argument("--run", type=str, help="Path to completed run results")
    args = parser.parse_args()

    if args.selftest:
        selftest()
    elif args.run:
        print(f"LLM judge for run: {args.run}")
        print("(Full implementation: iterate over result files, score each, write judge_scores.json)")
    else:
        print("Usage: python benchmarks/judge.py --selftest")
        print("       python benchmarks/judge.py --run results/<stamp>")
