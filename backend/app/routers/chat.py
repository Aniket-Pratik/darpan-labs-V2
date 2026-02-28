"""Twin chat API endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.chat import (
    BrandChatSessionItem,
    ChatHistoryResponse,
    TwinChatRequest,
    TwinChatResponse,
)
from app.services.twin_chat_service import TwinChatService, get_twin_chat_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/twins", tags=["Twin Chat"])


def get_service() -> TwinChatService:
    """Dependency for twin chat service."""
    return get_twin_chat_service()


class ChatSessionItem(BaseModel):
    """Chat session list item."""

    id: UUID
    twin_id: UUID
    created_by: UUID
    created_at: str
    message_count: int = 0


@router.get(
    "/brand-sessions",
    response_model=list[BrandChatSessionItem],
    summary="List brand chat sessions",
    description="Get all chat sessions created by a user (brand), with twin profile info.",
)
async def list_brand_sessions(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    service: TwinChatService = Depends(get_service),
):
    """List all brand chat sessions for a user."""
    try:
        return await service.get_brand_sessions(user_id, session)
    except Exception as e:
        logger.error(f"List brand sessions failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/{twin_id}/chat",
    response_model=TwinChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with a twin",
    description="""
    Send a message to a digital twin and get a response. The twin responds
    in-character based on its personality profile, grounded in interview evidence.

    Each response includes:
    - Confidence score and label (high/medium/low)
    - Evidence snippets used to generate the response
    - Coverage gaps (domains where more data would improve answers)
    - Suggested module to complete for better answers (if applicable)
    """,
)
async def chat_with_twin(
    twin_id: UUID,
    request: TwinChatRequest,
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    service: TwinChatService = Depends(get_service),
):
    """Send a message to a twin and get a response."""
    try:
        return await service.chat(
            twin_id=twin_id,
            message=request.message,
            user_id=user_id,
            db=session,
            session_id=request.session_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Twin chat failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}",
        )


@router.get(
    "/{twin_id}/chat/sessions",
    response_model=list[ChatSessionItem],
    summary="List chat sessions",
    description="Get all chat sessions for a twin.",
)
async def list_chat_sessions(
    twin_id: UUID,
    session: AsyncSession = Depends(get_session),
    service: TwinChatService = Depends(get_service),
):
    """List chat sessions for a twin."""
    try:
        sessions = await service.get_sessions(twin_id, session)
        return [
            ChatSessionItem(
                id=s.id,
                twin_id=s.twin_id,
                created_by=s.created_by,
                created_at=s.created_at.isoformat(),
                message_count=len(s.messages) if hasattr(s, "messages") and s.messages else 0,
            )
            for s in sessions
        ]
    except Exception as e:
        logger.error(f"List sessions failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/{twin_id}/chat/{session_id}/history",
    response_model=ChatHistoryResponse,
    summary="Get chat history",
    description="Get the full message history for a chat session.",
)
async def get_chat_history(
    twin_id: UUID,
    session_id: UUID,
    session: AsyncSession = Depends(get_session),
    service: TwinChatService = Depends(get_service),
):
    """Get chat history for a session."""
    try:
        return await service.get_chat_history(twin_id, session_id, session)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Get chat history failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
