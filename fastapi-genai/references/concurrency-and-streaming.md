# Concurrency & Streaming

## The Async Rule

Mark a route `async def` only if **every** dependency inside it is also async and properly
awaited. Mixing a sync client into an `async def` handler blocks the entire event loop for
every other request being served — worse than just leaving the handler synchronous and
letting FastAPI route it to its thread pool automatically.

```python
# Wrong: declares async but calls a sync client — blocks the event loop
@app.get("/bad")
async def bad(prompt: str):
    return sync_client.chat.completions.create(...)

# Right (option A): stay sync, FastAPI offloads to its thread pool
@app.get("/ok-sync")
def ok_sync(prompt: str):
    return sync_client.chat.completions.create(...)

# Right (option B): go fully async with the provider's async client
@app.get("/ok-async")
async def ok_async(prompt: str):
    return await async_client.chat.completions.create(...)
```

I/O-bound work (API calls, DB queries, file I/O) is what async buys you something on. CPU-
bound work (local model inference) isn't helped by `async`/`await` at all — that needs a
separate process/worker, not an `await`.

## Running Things Concurrently

```python
import asyncio

async def fetch_all(urls: list[str]) -> list[str]:
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*[fetch(session, u) for u in urls])
```

Use `asyncio.gather` for independent concurrent calls (e.g., fetching several URLs before
building a prompt) — don't await them sequentially in a loop if they don't depend on each
other.

## Streaming Text — Server-Sent Events (SSE)

The simplest one-way streaming mechanism; browsers' built-in `EventSource` handles
reconnection for you.

```python
from fastapi.responses import StreamingResponse

async def chat_stream(prompt: str):
    stream = await async_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="gpt-4o",
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        yield f"data: {delta}\n\n"
        await asyncio.sleep(0.05)  # throttle — see optimization-caching.md
    yield "data: [DONE]\n\n"

@app.get("/generate/text/stream")
async def stream_endpoint(prompt: str):
    return StreamingResponse(chat_stream(prompt), media_type="text/event-stream")
```

Set `media_type="text/event-stream"` and prefix every chunk with `data: ` — browsers'
`EventSource` parsing depends on that exact format. Use a `POST` + manual `fetch` stream
reader on the client (instead of `EventSource`, which only supports `GET`) when the request
needs a body (e.g., full conversation history).

## Bidirectional Streaming — WebSocket

Use when the client needs to send more input mid-stream (live chat, not just one prompt →
one stream).

```python
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

manager = ConnectionManager()

@app.websocket("/chat")
async def chat_ws(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            prompt = await websocket.receive_text()
            async for chunk in chat_stream(prompt):
                await websocket.send_text(chunk)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

Reconnect with exponential backoff on the client — unlike SSE's `EventSource`, browsers
don't auto-reconnect a dropped `WebSocket` for you.

## SSE vs. WebSocket — Pick Based on Direction

| | SSE | WebSocket |
|---|---|---|
| Direction | Server → client only | Bidirectional |
| Client reconnect | Automatic (`EventSource`) | Manual — implement backoff yourself |
| Use for | Token streaming, one prompt → one response | Live chat, multi-turn within one connection |

Default to SSE unless the client genuinely needs to push more input mid-stream — it's
simpler and the browser handles reconnection for free.

## Persisting a Streamed Response — Background Tasks

You can't hold a database transaction open for the duration of a stream. Persist after the
stream completes, via a background task, not inline in the generator.

```python
from fastapi import BackgroundTasks
from itertools import tee

async def store_message(prompt: str, full_response: str, conversation_id: int, session):
    await MessageRepository(session).create(prompt, full_response, conversation_id)

@app.get("/chat/stream")
async def stream_and_store(prompt: str, background_tasks: BackgroundTasks, session=Depends(get_db_session)):
    stream_for_client, stream_for_storage = tee(chat_stream(prompt))
    background_tasks.add_task(store_message, prompt, "".join(stream_for_storage), conversation_id, session)
    return StreamingResponse(stream_for_client, media_type="text/event-stream")
```

`BackgroundTasks` is sufficient for "do this after the response is sent" work in most
services. Reach for an actual task queue (Celery, etc.) only once you have a measured need
— retries across process restarts, distributed workers, scheduled jobs — not by default.
