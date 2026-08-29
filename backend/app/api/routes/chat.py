from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import ChatSession, ChatMessage, User
from app.schemas.chat import ChatSessionOut, ChatMessageOut, SendMessageRequest, SendMessageResponse
from app.services.chat import send_message

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/sessions", response_model=list[ChatSessionOut])
async def list_sessions(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(ChatSession)
            .where(ChatSession.merchant_id == current_user.merchant_id)
            .order_by(ChatSession.created_at.desc())
        )
    ).scalars().all()
    return list(rows)


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageOut])
async def get_session_messages(
    session_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    rows = (
        await db.execute(
            select(ChatMessage)
            .join(ChatSession, ChatSession.id == ChatMessage.session_id)
            .where(ChatMessage.session_id == session_id, ChatSession.merchant_id == current_user.merchant_id)
            .order_by(ChatMessage.created_at.asc())
        )
    ).scalars().all()
    return list(rows)


@router.post("/messages", response_model=SendMessageResponse)
async def post_message(
    payload: SendMessageRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    session_id, reply, tools_called = await send_message(
        db=db,
        merchant_id=current_user.merchant_id,
        user_id=current_user.id,
        session_id=payload.session_id,
        message=payload.message,
    )
    return SendMessageResponse(session_id=session_id, reply=reply, tool_calls_made=tools_called)
