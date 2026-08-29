from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.gemini_client import run_agent_turn, AgentNotConfiguredError
from app.models import ChatSession, ChatMessage
from app.services.embedding import embed_text

RECENT_MESSAGE_WINDOW = 10
SEMANTIC_MEMORY_TOP_K = 3


async def get_or_create_session(db: AsyncSession, merchant_id: UUID, user_id: UUID, session_id: UUID | None) -> ChatSession:
    if session_id:
        session = await db.get(ChatSession, session_id)
        if session and session.merchant_id == merchant_id:
            return session

    session = ChatSession(merchant_id=merchant_id, user_id=user_id, title="New conversation")
    db.add(session)
    await db.flush()
    return session


async def _recent_messages(db: AsyncSession, session_id: UUID) -> list[ChatMessage]:
    rows = (
        await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(RECENT_MESSAGE_WINDOW)
        )
    ).scalars().all()
    return list(reversed(rows))


async def _semantic_memory(db: AsyncSession, merchant_id: UUID, query_embedding: list[float], exclude_ids: set[UUID]) -> list[ChatMessage]:
    """Finds past messages across this merchant's chat history whose embedding is
    closest to the current query -- this is what lets the agent recall a
    relevant conversation from last week even though it's outside the recent
    fixed-size window."""
    rows = (
        await db.execute(
            select(ChatMessage)
            .join(ChatSession, ChatSession.id == ChatMessage.session_id)
            .where(ChatSession.merchant_id == merchant_id, ChatMessage.embedding.is_not(None))
            .order_by(ChatMessage.embedding.cosine_distance(query_embedding))
            .limit(SEMANTIC_MEMORY_TOP_K + len(exclude_ids))
        )
    ).scalars().all()
    return [m for m in rows if m.id not in exclude_ids][:SEMANTIC_MEMORY_TOP_K]


def _to_agent_role(role: str) -> str:
    """Normalizes a stored message role into the generic "user"/"assistant"
    shape `run_agent_turn` expects -- the provider-specific role mapping
    (e.g. Gemini's "model" role) happens inside the agent client."""
    return "assistant" if role == "assistant" else "user"


async def send_message(
    *, db: AsyncSession, merchant_id: UUID, user_id: UUID, session_id: UUID | None, message: str
) -> tuple[UUID, str, list[str]]:
    session = await get_or_create_session(db, merchant_id, user_id, session_id)

    query_embedding = embed_text(message)

    recent = await _recent_messages(db, session.id)
    recent_ids = {m.id for m in recent}
    memory = await _semantic_memory(db, merchant_id, query_embedding, exclude_ids=recent_ids)

    extra_context = None
    if memory:
        lines = [f'- ({m.role}, earlier conversation): "{m.content[:300]}"' for m in memory]
        extra_context = "Potentially relevant earlier context from this merchant's chat history:\n" + "\n".join(lines)

    conversation = [{"role": _to_agent_role(m.role), "content": m.content} for m in recent]
    conversation.append({"role": "user", "content": message})

    user_msg = ChatMessage(session_id=session.id, role="user", content=message, embedding=query_embedding)
    db.add(user_msg)

    try:
        reply_text, tools_called = await run_agent_turn(
            db=db, merchant_id=merchant_id, conversation=conversation, extra_context=extra_context
        )
    except AgentNotConfiguredError:
        reply_text = (
            "The AI chat agent isn't configured yet -- GEMINI_API_KEY is missing on the server. "
            "Every other MerchantGPT feature (dashboard, revenue leaks, segmentation, churn, cart recovery, "
            "reports) works without it; only this conversational chat needs a Gemini API key."
        )
        tools_called = []

    assistant_msg = ChatMessage(
        session_id=session.id, role="assistant", content=reply_text, embedding=embed_text(reply_text)
    )
    db.add(assistant_msg)

    if session.title == "New conversation":
        session.title = message[:60] + ("..." if len(message) > 60 else "")

    await db.commit()
    return session.id, reply_text, tools_called
