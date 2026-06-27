#!/usr/bin/env python3
"""Scorer selftest: validates every deterministic scorer before API spend.

For each task, the 'good' reference must score correct+safe (all axes pass),
and the 'bad' reference must fail on its declared axis.

Run: python benchmarks/selftest.py

This is the single most important file in the evaluation pipeline.
If your instruments are broken, every number that follows is noise.
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from benchmarks.tasks import TASKS
except ImportError:
    # Tasks not yet defined — selftest passes trivially
    print("No tasks defined yet. Define TASKS in benchmarks/tasks.py first.")
    sys.exit(0)


def selftest():
    """For each task, good ref must pass all axes; bad ref must fail declared axis."""
    failures = 0
    passed = 0
    skipped = 0

    for task_id, task in TASKS.items():
        # Skip tasks without references (open-ended measurement tasks)
        if task.get("open"):
            skipped += 1
            continue

        axis = task.get("axis", "safe")

        for kind in ("good", "bad"):
            try:
                result = task["score"](task[kind])
            except Exception as e:
                print(f"XX {task_id:30} {kind:4} SCORER CRASHED: {e}")
                failures += 1
                continue

            if kind == "good":
                ok = result.get("correct", 0) == 1 and result.get("safe", 0) == 1
            else:
                ok = result.get(axis, 1) == 0

            status = "ok " if ok else "XX "
            print(f"{status} {task_id:30} {kind:4} "
                  f"correct={result.get('correct','?')} safe={result.get('safe','?')} "
                  f"axis={axis}  reason={result.get('reason','?')[:80]}")

            if ok:
                passed += 1
            else:
                failures += 1

    print(f"\n---")
    print(f"passed: {passed}  failed: {failures}  skipped (open): {skipped}")
    if failures:
        print(f"\n❌ {failures} scorer(s) failed selftest. Fix before any API spend.")
        sys.exit(1)
    else:
        print(f"\n✅ All scorers validated. Instruments are trustworthy.")
        sys.exit(0)


if __name__ == "__main__":
    selftest()
