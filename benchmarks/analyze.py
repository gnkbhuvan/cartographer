#!/usr/bin/env python3
"""Analyze benchmark results — produces comparison tables.

Usage:
  python benchmarks/analyze.py results/<stamp>/results.json
"""

import json
import sys
from pathlib import Path

SKILL_MAP = {
    "pe-clarify": "prompt-engineering",
    "pe-debug": "prompt-engineering",
    "ag-necessity": "agentic-ai",
    "ag-tools": "agentic-ai",
    "fa-lifespan": "fastapi-genai",
    "fa-ratelimit": "fastapi-genai",
    "rag-necessity": "production-rag",
    "rag-vectordb": "production-rag",
}


def analyze(results_path: str):
    data = json.loads(Path(results_path).read_text())

    # Per-task comparison
    print("=" * 95)
    print(" PER-TASK COMPARISON")
    print("=" * 95)
    print(f"{'Task':<20} {'Skill':<22} {'No-Skill':<10} {'Skill':<10} {'Winner':<10}")
    print("-" * 95)

    by_skill = {}
    for task_id in SKILL_MAP:
        skill = SKILL_MAP[task_id]
        no_skill = [r for r in data if r["task"] == task_id and r["arm"] == "no-skill"]
        with_skill = [r for r in data if r["task"] == task_id and r["arm"] == "skill"]

        ns_score = no_skill[0]["score"]["correct"] if no_skill else "?"
        ws_score = with_skill[0]["score"]["correct"] if with_skill else "?"

        if ns_score == 1 and ws_score == 1:
            winner = "tie ✓✓"
        elif ns_score == 1:
            winner = "regression ⚠"
        elif ws_score == 1:
            winner = "SKILL WINS ✅"
        else:
            winner = "both fail ❌"

        print(f"{task_id:<20} {skill:<22} {str(ns_score):<10} {str(ws_score):<10} {winner:<10}")

        if skill not in by_skill:
            by_skill[skill] = {"no_skill_correct": 0, "skill_correct": 0, "total": 0}
        by_skill[skill]["no_skill_correct"] += ns_score if isinstance(ns_score, int) else 0
        by_skill[skill]["skill_correct"] += ws_score if isinstance(ws_score, int) else 0
        by_skill[skill]["total"] += 1

    # Per-skill aggregate
    print(f"\n{'=' * 80}")
    print(" PER-SKILL AGGREGATE")
    print(f"{'=' * 80}")
    print(f"{'Skill':<22} {'No-Skill':<12} {'With Skill':<12} {'Delta':<10}")
    print("-" * 60)
    for skill, scores in by_skill.items():
        ns_rate = scores["no_skill_correct"] / scores["total"] * 100 if scores["total"] else 0
        ws_rate = scores["skill_correct"] / scores["total"] * 100 if scores["total"] else 0
        delta = ws_rate - ns_rate
        delta_str = f"+{delta:.0f}%" if delta > 0 else f"{delta:.0f}%" if delta < 0 else "—"
        print(f"{skill:<22} {ns_rate:.0f}% ({scores['no_skill_correct']}/{scores['total']})     "
              f"{ws_rate:.0f}% ({scores['skill_correct']}/{scores['total']})     {delta_str}")

    # Overall
    total_ns = sum(s["no_skill_correct"] for s in by_skill.values())
    total_ws = sum(s["skill_correct"] for s in by_skill.values())
    total = sum(s["total"] for s in by_skill.values())
    print(f"\n{'─' * 60}")
    print(f"{'OVERALL':<22} {total_ns/total*100:.0f}% ({total_ns}/{total})     "
          f"{total_ws/total*100:.0f}% ({total_ws}/{total})     "
          f"{'+' if total_ws > total_ns else ''}{total_ws - total_ns} tasks")

    # Cost summary
    total_cost = sum(r.get("metadata", {}).get("cost", 0) for r in data)
    total_tokens = sum(r.get("metadata", {}).get("tokens", {}).get("total", 0) for r in data)
    print(f"\n  Total cost: ${total_cost:.4f}")
    print(f"  Total tokens: {total_tokens}")

    # Per-task details
    print(f"\n{'=' * 95}")
    print(" DETAILED OUTPUTS")
    print(f"{'=' * 95}")
    for r in data:
        score = r.get("score", {})
        print(f"\n--- {r['task']} [{r['arm']}] ---")
        print(f"  Score: correct={score.get('correct')} safe={score.get('safe')}")
        print(f"  Reason: {score.get('reason', '?')}")
        print(f"  Tokens: {r.get('metadata',{}).get('tokens',{}).get('total','?')}  "
              f"Cost: ${r.get('metadata',{}).get('cost',0):.4f}")
        output = r.get("output", "")
        if len(output) > 300:
            output = output[:300] + "..."
        print(f"  Output: {output}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Find latest results
        results_dir = Path(__file__).resolve().parent / "results"
        runs = sorted([d for d in results_dir.iterdir() if d.is_dir() and (d / "results.json").exists()])
        if runs:
            results_path = runs[-1] / "results.json"
            print(f"Analyzing latest: {results_path}\n")
        else:
            print("No results found. Run benchmark first.")
            sys.exit(1)
    else:
        results_path = sys.argv[1]

    analyze(results_path)
