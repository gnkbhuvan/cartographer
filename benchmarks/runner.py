#!/usr/bin/env python3
"""Real benchmark: test each skill via Deepseek API."""
import json, os, sys, time, urllib.request, ssl
from pathlib import Path

# macOS SSL workaround
SSL_CONTEXT = ssl.create_default_context()
try:
    import certifi
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from benchmarks.tasks import TASKS

# Load API key: try env first, then Hermes .env file
def _load_key():
    k = os.environ.get("OPENCODE_GO_API_KEY", "").strip()
    if k: return k
    try:
        for line in open(os.path.expanduser("~/.hermes/.env"), "r"):
            # line format: OPENCODE_GO_API_KEY=sk-...
            if line.startswith("OPENCODE_GO_API_KEY="):
                k = line.split("=", 1)[1].strip()
                if k: return k
    except Exception:
        pass
    return ""

API_KEY = _load_key()
if not API_KEY:
    print("No API key. Set OPENCODE_GO_API_KEY or ensure ~/.hermes/.env has it.")
    sys.exit(1)

BASE_URL = "https://opencode.ai/zen/go/v1"
MODEL = "deepseek-v4-pro"
SKILLS_DIR = Path(__file__).resolve().parent.parent

def load_skill(name):
    p = SKILLS_DIR / name / "SKILL.md"
    if not p.exists():
        return None
    text = p.read_text()
    if text.startswith("---"):
        parts = text.split("---", 2)
        text = parts[2] if len(parts) >= 3 else text
    return text.strip()

TASK_SKILL = {
    "pe-clarify": "prompt-engineering", "pe-debug": "prompt-engineering",
    "ag-necessity": "agentic-ai", "ag-tools": "agentic-ai",
    "fa-lifespan": "fastapi-genai", "fa-ratelimit": "fastapi-genai",
    "rag-necessity": "production-rag", "rag-vectordb": "production-rag",
}

def call(system_prompt, user_prompt, temp=0.3):
    body = json.dumps({
        "model": MODEL, "temperature": temp,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions", data=body,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180, context=SSL_CONTEXT) as r:
            resp = json.loads(r.read())
        return resp["choices"][0]["message"]["content"]
    except Exception as e:
        return f"API_ERROR: {e}"

results = []
SYSTEM_BASE = "You are an AI engineer. Be concise."

for task_id, task in TASKS.items():
    skill_name = TASK_SKILL.get(task_id)
    if not skill_name:
        continue
    skill_text = load_skill(skill_name)

    print(f"\n{'='*60}")
    print(f"TASK: {task_id} ({skill_name})")
    print(f"{'='*60}")

    # Without skill
    print("→ Without skill...", end=" ", flush=True)
    out_no = call(SYSTEM_BASE, task["prompt"])
    print(f"{len(out_no)} chars")

    # With skill
    print("→ With skill...", end=" ", flush=True)
    sys_with = f"{SYSTEM_BASE}\n\nFollow this skill:\n\n{skill_text}"
    out_with = call(sys_with, task["prompt"])
    print(f"{len(out_with)} chars")

    scorer = task["score"]
    s_no = scorer(out_no)
    s_with = scorer(out_with)

    results.append({
        "task": task_id, "skill": skill_name,
        "no_skill": {"correct": s_no["correct"], "safe": s_no["safe"], "reason": s_no["reason"], "len": len(out_no)},
        "with_skill": {"correct": s_with["correct"], "safe": s_with["safe"], "reason": s_with["reason"], "len": len(out_with)},
    })
    print(f"   NO skill:  corr={s_no['correct']} safe={s_no['safe']} | {s_no['reason'][:80]}")
    print(f"   WITH skill: corr={s_with['correct']} safe={s_with['safe']} | {s_with['reason'][:80]}")
    time.sleep(0.5)

# Summary
nc = sum(1 for r in results if r["no_skill"]["correct"])
wc = sum(1 for r in results if r["with_skill"]["correct"])
print(f"\n{'='*60}")
print(f"FINAL: No-skill correct={nc}/{len(results)} | With-skill correct={wc}/{len(results)}")
print(f"{'='*60}")
for r in results:
    d = r["with_skill"]["correct"] - r["no_skill"]["correct"]
    a = "↑" if d > 0 else ("↓" if d < 0 else "→")
    print(f"  {r['task']:20} no={r['no_skill']['correct']} with={r['with_skill']['correct']} {a} | no_len={r['no_skill']['len']:4d} with_len={r['with_skill']['len']:4d}")
