# Auth & AI-Specific Security

## Authentication — Pick by Stakes

| Method | Use for | Notes |
|---|---|---|
| **Basic** | Local prototyping only | Compare credentials with `secrets.compare_digest` to avoid timing attacks — never `==` |
| **JWT** | Most production APIs | Short-lived access tokens; store a revocation record so logout actually invalidates a token |
| **OAuth2** | Delegating to GitHub/Google/etc. | CSRF `state` token must be stored server-side (session), never trusted from the client round-trip alone |

```python
import secrets
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

def authenticate(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    ok_user = secrets.compare_digest(credentials.username.encode(), b"expected_user")
    ok_pass = secrets.compare_digest(credentials.password.encode(), b"expected_pass")
    if not (ok_user and ok_pass):
        raise HTTPException(status_code=401, detail="Incorrect credentials",
                             headers={"WWW-Authenticate": "Basic"})
    return credentials.username
```

**JWT pattern**: hash passwords with bcrypt (auto-salts, defeats rainbow tables), issue a
token with `exp`/`iss`/a DB-backed `token_id`, and check that `token_id` is still active on
every protected request — this is what makes logout actually work, since a stateless JWT
alone can't be revoked.

## Authorization — Match Complexity to the Actual Need

- **RBAC** (role-based): fixed roles like `USER`/`ADMIN` with fixed permissions. Start here.
- **ABAC** (attribute-based): gate on an attribute, e.g. subscription tier. Add when RBAC's
  fixed roles can't express the rule.
- **ReBAC** (relationship-based): gate on a relationship, e.g. "member of this team owns
  this resource." Add when permissions are inherited from a parent object.

```python
async def is_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Not allowed")
    return user
```

**Enforce authorization in application code, not in the prompt.** A system-prompt
instruction like "only let admins do X" is not a security control — the model can be
prompt-injected around it. The `Depends()` check above runs before the model is ever
called.

## AI-Specific Threats (OWASP-style)

Prompt injection (bypass instructions / extract secrets), insecure output handling
(executing model-generated code without sanitizing it), training-data/RAG poisoning,
denial-of-service via huge payloads or high concurrency, sensitive-data leakage (PII
echoed back), excessive agency (an agent takes a consequential action without a gate — see
the `agentic-ai` skill), and overreliance (a wrong answer taken as authoritative because it
came from a model).

## Input Guardrails — Run Concurrently, Cancel on Failure

```python
async def is_topic_allowed(query: str) -> bool:
    verdict = await guardrail_client.invoke(query)  # cheap classifier call
    return verdict == "allowed"

async def invoke_with_guardrail(query: str) -> str:
    guard_task = asyncio.create_task(is_topic_allowed(query))
    main_task = asyncio.create_task(llm_client.invoke(query))
    done, _ = await asyncio.wait([guard_task, main_task], return_when=asyncio.FIRST_COMPLETED)
    if guard_task in done and not await guard_task:
        main_task.cancel()
        return "Sorry, that's outside what I can help with."
    return await main_task
```

Run the guardrail concurrently with the main call, not before it sequentially — and cancel
the main call if the guardrail fails, so you're not paying for tokens on a request you're
about to reject anyway.

## Output Guardrails

Score the model's own output against an explicit, narrow criterion (toxicity, PII
presence, JSON validity, domain-relevance) using a cheap classifier or a second model call
— and remember an LLM-based check is probabilistic, not a hard guarantee; pair it with a
deterministic check (e.g., a regex for PII patterns, a JSON-parse check) wherever one
exists.

## Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["200/day", "60/hour"])
app.state.limiter = limiter

@app.post("/generate/text")
@limiter.limit("5/minute")
def generate_text(request: Request): ...

@app.post("/generate/image")
@limiter.limit("1/minute")  # stricter for the more expensive endpoint
def generate_image(request: Request): ...
```

**Per-user limits beat per-IP** — IP-based limits are trivially defeated by proxies/VPNs;
key the limiter by authenticated user ID wherever auth exists. **Distributed deployments**
need a shared backend (Redis) for the limiter — independent in-process counters per
instance make quotas meaningless once you're behind a load balancer with more than one
replica.
