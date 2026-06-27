# Testing AI Services

## Why This Is Different From Testing Normal Endpoints

The model is non-deterministic — asserting exact output strings is a test that will flake
or fail on a correct response. Test **properties** of the output (length, readability,
absence of toxicity, valid JSON, presence of an expected entity) instead of exact matches.

**Strategy shape**: favor a "trophy" distribution (a little static checking, solid unit
tests, *substantial* integration tests, a thin layer of E2E) over a classic test pyramid —
for AI services, integration tests (does the retrieval/generation pipeline actually behave
correctly end to end) carry more of the real risk than pure unit tests do.

## pytest Basics

```python
import pytest

@pytest.fixture(scope="module")
def tokens():
    return [1, 2, 3, 4, 5]

@pytest.mark.parametrize("tokens, chunk_size, expected", [
    ([1, 2, 3, 4, 5], 2, [[1, 2], [3, 4], [5]]),
    ([], 3, []),                       # empty/valid
    ([1, 2, 3], 5, [[1, 2, 3]]),        # boundary
])
def test_chunking(tokens, chunk_size, expected):
    assert chunk(tokens, chunk_size) == expected

@pytest.mark.asyncio
async def test_async_search(async_db_client):
    result = await async_db_client.search(query_vector=[0.1, 0.2], limit=1)
    assert result is not None
```

Use fixtures with explicit setup/teardown (`yield` then cleanup) for anything stateful —
DB connections, test collections — and parametrize across valid, invalid, and boundary
inputs rather than writing one test per case by hand.

## Test Doubles — Use the Right One

| Type | Behavior | Use for |
|---|---|---|
| **Dummy** | Returns a fixed value, never inspected | Filling a required parameter you don't care about in this test |
| **Stub** | Returns canned responses based on input | Driving a specific code path without a real model call |
| **Spy** | Stub + records calls made to it | Asserting the code called the model the right number of times, with the right args |
| **Mock** | Stub + behavior verification built in (`pytest-mock`) | Same as spy, with less boilerplate |
| **Fake** | A simplified but real working implementation (e.g., in-memory cache) | Integration-style tests that need real behavior, just lighter-weight |

```python
def test_process_query_with_mock(mocker):
    llm_client = mocker.Mock()
    llm_client.invoke.return_value = "mock response"
    process_query("some query", llm_client)
    llm_client.invoke.assert_called_once_with("some query")
```

Use mocks/stubs in unit tests to avoid real API calls (cost, latency, flakiness); use real
calls only in a smaller set of integration/E2E tests that specifically validate the live
behavior.

## Behavioral Testing (For the Non-Deterministic Parts)

**Minimum functionality test** — a property the output must have:

```python
import textstat

@pytest.mark.parametrize("prompt, min_score", [
    ("Explain this as simply as possible", 80),
])
def test_readability_floor(prompt, min_score):
    response = llm_client.invoke(prompt)
    assert textstat.flesch_reading_ease(response) > min_score
```

**Invariance test** — output property should hold despite irrelevant input changes
(casing, minor typos):

```python
@pytest.mark.parametrize("variant", [base_prompt, base_prompt.upper(), base_prompt + " please"])
def test_readability_invariant_to_phrasing(variant):
    response = llm_client.invoke(variant)
    assert textstat.flesch_reading_ease(response) > 50
```

**Directional expectation test** — output should change in a predictable *direction* given
a more complex/different input:

```python
def test_more_detailed_prompt_yields_longer_response():
    short = llm_client.invoke("Explain X")
    long = llm_client.invoke("Explain X in full detail with examples")
    assert len(long) > len(short)
```

**Auto-evaluation** (a model checks a property of another model's output) — useful for
toxicity/safety checks, but it's a probabilistic signal, not a guarantee; pair it with a
deterministic check wherever one exists (regex, schema validation).

## Integration Testing — Retrieval Precision/Recall

```python
def calculate_recall(expected: list, retrieved: list) -> float:
    return len(set(expected) & set(retrieved)) / len(expected)

@pytest.mark.parametrize("query_vector, expected_ids", [([0.1, 0.2, 0.3], [1, 2, 3])])
def test_retrieval_quality(db_client, query_vector, expected_ids):
    retrieved = [p.id for p in db_client.search(query_vector=query_vector, limit=3)]
    assert calculate_recall(expected_ids, retrieved) >= 0.66
```

## End-to-End Testing

Test the full user-facing workflow, not just one layer:

```python
@pytest.mark.asyncio
async def test_full_rag_workflow(test_client):
    upload = await test_client.post("/upload", files={"file": ("doc.txt", b"Some fact", "text/plain")})
    assert upload.status_code == 200

    answer = await test_client.post("/generate", json={"query": "What's the fact?"})
    assert "fact" in answer.json()["response"]
```

Run E2E tests less frequently than unit/integration (they're slow and the most expensive
in tokens/cost) — they exist to catch integration gaps the lower layers can't see, not to
be the primary safety net.

## Common Mistake to Avoid

100% code coverage is not the same as validation that the service does the right thing —
a test suite that exercises every line but never checks output quality on a representative
set of real prompts has not actually tested the AI behavior, only the plumbing around it.
