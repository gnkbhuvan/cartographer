# Project Setup & Model Serving

## Core Endpoint Shape

```python
from fastapi import FastAPI
from openai import OpenAI

app = FastAPI()
openai_client = OpenAI(api_key="...")

@app.post("/chat")
def chat_controller(prompt: str):
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    return {"statement": response.choices[0].message.content}
```

Type-annotate the request/response — FastAPI auto-validates and documents from Pydantic
models (see `type-safety.md`); don't hand-roll validation you get for free.

## Loading Models/Clients Once — Lifespan Events

The single highest-leverage pattern in this whole skill: load anything expensive (a local
model, a DB engine, an AI client) once at startup, not on every request.

```python
from contextlib import asynccontextmanager
from typing import AsyncIterator

models: dict = {}

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    models["text2image"] = load_image_model()   # startup
    yield
    models.clear()                                # shutdown cleanup

app = FastAPI(lifespan=lifespan)

@app.get("/generate/image")
def serve_image(prompt: str):
    pipe = models["text2image"]
    return Response(content=img_to_bytes(generate_image(pipe, prompt)), media_type="image/png")
```

## Model-Serving Strategies — Pick One Deliberately

| Strategy | When | Trade-off |
|---|---|---|
| **Load per request** | Prototyping, memory-constrained, swapping models often | Simple but adds reload latency to every request — avoid in production |
| **Preload via lifespan** | The default for production | Persistent RAM/VRAM use, but no reload latency |
| **External model server** (e.g. a dedicated inference server) proxied through FastAPI | Self-hosted models at real scale — batching/GPU-scheduling benefit from a dedicated server | FastAPI becomes a thin proxy (auth/routing/validation); inference logic lives elsewhere |
| **Third-party API** (OpenAI/Anthropic/etc.) | Default unless you have a specific reason to self-host | No infra to manage, but data leaves your boundary — check compliance requirements first |

Default to the third-party-API or preload-via-lifespan strategies; only reach for an
external model server once you have a measured reason (GPU scheduling, batching, model size)
— per the "don't add infrastructure before you need it" axiom in `SKILL.md`.

## Dependency Injection

```python
from fastapi import Depends

def get_db():
    db = create_session()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/{email}/messages")
def get_messages(email: str, db = Depends(get_db)):
    return db.query(...)
```

`Depends()` results are cached per-request and support nested/hierarchical injection — use
it for anything that needs setup/teardown per request: DB sessions, auth checks, shared AI
clients.

## Middleware for Cross-Cutting Concerns

```python
import time, uuid
from datetime import datetime, timezone

@app.middleware("http")
async def monitor_service(req, call_next):
    request_id = uuid.uuid4().hex
    start = time.perf_counter()
    response = await call_next(req)
    response.headers["X-Response-Time"] = str(round(time.perf_counter() - start, 3))
    response.headers["X-Request-ID"] = request_id
    return response
```

Use middleware for logging, request IDs, response-time headers, and CORS — anything that
should run once per request rather than being duplicated in every handler.

## Inference Parameters That Matter

When serving a self-hosted/local model directly (vs. calling a hosted provider API):
`temperature` (lower = deterministic, higher = varied), `max_new_tokens` (caps output
length — set this, don't let generation run unbounded), `do_sample` (False = greedy/
deterministic, True = sampling), `top_k`/`top_p` (restrict the sampling pool for quality).
Set a manual seed (`torch.manual_seed(...)`) when reproducibility matters more than variety.
