# Type Safety for AI Services

## Request/Response Contracts

```python
from pydantic import BaseModel
from typing import Literal
from datetime import datetime

class TextModelRequest(BaseModel):
    model: Literal["gpt-4o", "gpt-4o-mini"]
    prompt: str
    temperature: float = 0.0

class TextModelResponse(BaseModel):
    content: str | None
    tokens: int
    created_at: datetime = datetime.now()
```

## Constrained Fields

```python
from typing import Annotated
from pydantic import Field, PositiveInt, HttpUrl

class ModelRequest(BaseModel):
    prompt: Annotated[str, Field(min_length=1, max_length=5000)]

class ImageModelRequest(ModelRequest):
    output_size: Annotated[tuple[PositiveInt, PositiveInt], "width, height"]
    num_inference_steps: Annotated[int, Field(ge=0, le=2000)] = 200
```

Constrain at the field level (length, range, regex) rather than checking manually inside
the handler — it's enforced before your code runs and shows up correctly in the OpenAPI
schema.

## Custom Validators — Coercing/Rejecting Bad LLM Output

```python
from pydantic import AfterValidator, validate_call

@validate_call
def is_square_image(value: tuple[int, int]) -> tuple[int, int]:
    if value[0] != value[1] or value[0] not in (512, 1024):
        raise ValueError(f"Invalid size: {value}")
    return value

OutputSize = Annotated[tuple[int, int], AfterValidator(is_square_image)]
```

This is the mechanism for enforcing "the model is an untrusted dependency" in practice:
validate everything that comes back from a model call against an explicit schema before
it goes anywhere else in your system.

## Computed Fields

```python
from pydantic import computed_field

class TextModelResponse(BaseModel):
    content: str
    price_per_token: float = 0.0

    @computed_field
    @property
    def tokens(self) -> int:
        return count_tokens(self.content)

    @computed_field
    @property
    def cost(self) -> float:
        return self.price_per_token * self.tokens
```

Use computed fields for anything derived (cost, token count) rather than computing it in
the handler and stuffing it into the response by hand — keeps the derivation co-located
with the model it describes.

## Environment/Settings Validation

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, HttpUrl

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    port: int = 8000
    app_secret: Annotated[str, Field(min_length=16)]
    pg_dsn: Annotated[PostgresDsn, Field(alias="DATABASE_URL")]
    cors_whitelist: Annotated[set[HttpUrl], Field(alias="CORS_WHITELIST")]

settings = AppSettings()
```

Validate configuration the same way you validate requests — a malformed `DATABASE_URL`
should fail at startup, not three layers deep into a request handler at 2am.

## Structured Outputs from the Model

**Native support** (when the provider offers it — prefer this):

```python
from pydantic import BaseModel, Field

class DocumentClassification(BaseModel):
    category: str = Field(..., description="The category")

response = await client.beta.chat.completions.create(
    model="gpt-4o",
    messages=[...],
    response_format=DocumentClassification,
)
```

**Prefill fallback** (when native structured-output mode isn't available): seed the
assistant's response with the opening of the expected structure, so the model continues
the pattern instead of choosing its own format.

```python
response = await client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "Classify the document. Respond in JSON: {category: ...}"},
        {"role": "user", "content": title},
        {"role": "assistant", "content": "The classification is {"},  # prefill
    ],
)
try:
    return json.loads("{" + response.choices[0].message.content)
except json.JSONDecodeError:
    return {"error": "model returned an unparseable response"}
```

Always wrap the parse in a try/except — a model that "usually" returns valid JSON will
eventually not, and that failure needs a defined behavior, not an unhandled crash.
