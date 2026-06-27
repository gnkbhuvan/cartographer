# Database Integration

## Do You Need a Database At All?

Skip it if data loss is tolerable, recomputation is cheap, and nothing needs to be shared
across sessions or instances (e.g., a stateless demo image generator). Add one once you
need to persist conversation history, track usage/cost, or share state across requests or
instances.

## Async Engine & Session Setup

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from contextlib import asynccontextmanager

engine = create_async_engine("postgresql+psycopg://user:pass@localhost/db", echo=True)
async_session = async_sessionmaker(bind=engine, class_=AsyncSession, autocommit=False, autoflush=False)

@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

async def get_db_session():
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

`autocommit=False, autoflush=False` gives explicit transaction control — don't let the ORM
write things you didn't intentionally commit.

## Schema for AI-Service Data

```python
class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[int] = mapped_column(primary_key=True)
    model_type: Mapped[str] = mapped_column(index=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )

class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"))
    prompt_content: Mapped[str] = mapped_column()
    response_content: Mapped[str] = mapped_column()
    prompt_tokens: Mapped[int | None] = mapped_column()
    response_tokens: Mapped[int | None] = mapped_column()
    is_success: Mapped[bool | None] = mapped_column()
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
```

Track token counts and success/failure per message from day one — this is what makes
usage billing, cost analysis, and debugging possible later without a schema migration.
`cascade="all, delete-orphan"` on the relationship means deleting a conversation correctly
deletes its messages, not leaving orphans.

## Repository / Service Pattern

Separate raw data access (repository) from business logic (service) so endpoints stay thin
and logic is testable without a real database (see `testing.md`'s test-double patterns).

```python
class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: ConversationCreate) -> Conversation:
        conv = Conversation(**data.dict())
        self.session.add(conv)
        await self.session.commit()
        await self.session.refresh(conv)
        return conv

class ConversationService(ConversationRepository):
    async def list_messages(self, conversation_id: int) -> list[Message]:
        result = await self.session.execute(
            select(Message).where(Message.conversation_id == conversation_id)
        )
        return list(result.scalars().all())

@router.post("/conversations", status_code=201)
async def create_conversation(body: ConversationCreate, session=Depends(get_db_session)) -> ConversationOut:
    conv = await ConversationService(session).create(body)
    return ConversationOut.model_validate(conv)
```

## Migrations

```bash
pip install alembic
alembic init
# point alembic/env.py's target_metadata at your Base.metadata
alembic revision --autogenerate -m "add conversations and messages"
alembic upgrade head
```

Never hand-edit a migration file after it's been applied anywhere — write a new migration
for any further change, the same way you wouldn't rewrite a merged git commit.

## Streaming + Persistence Together

See `concurrency-and-streaming.md`'s background-task pattern — you cannot hold this
session open for the duration of a stream; persist via `BackgroundTasks` after the stream
finishes, not inside the generator.
