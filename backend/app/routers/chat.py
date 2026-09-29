"""
POST /api/chat/session   — create a new chat session, returns session_id
POST /api/chat/message   — send a message, returns PAWAI's reply

Authentication: existing HttpOnly session cookie (same as every other route).
GEMINI_API_KEY never leaves the backend.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_user
from app.models.user import User
import app.services.pawai_chat_service as chat_svc

router = APIRouter(prefix="/api/chat", tags=["chat"])


# ── Request / Response schemas ───────────────────────────────────────────────

class StartSessionRequest(BaseModel):
    """
    Sent by chatbot.html when it first opens.
    Contains the analysis context produced by the ML + Gemini pipeline.
    """
    emotion:           str  | None = Field(default=None)
    confidence:        float | None = Field(default=None)
    ai_interpretation: str  | None = Field(default=None)
    filename:          str  | None = Field(default=None)
    media_id:          str  | None = Field(default=None)
    sampled_frames:    int  | None = Field(default=None)
    duration:          float | None = Field(default=None)


class StartSessionResponse(BaseModel):
    session_id: str


class SendMessageRequest(BaseModel):
    session_id: str = Field(min_length=1)
    message:    str = Field(min_length=1, max_length=4000)


class SendMessageResponse(BaseModel):
    reply: str


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post(
    "/session",
    response_model=StartSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_session(
    payload: StartSessionRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new PAWAI chat session for the authenticated user.
    Returns an opaque session_id the frontend sends with every message.
    The session_id never contains user credentials or API keys.
    """
    context = payload.model_dump()           # plain dict, safe to store
    session_id = chat_svc.create_session(
        user_id=str(user.id),
        context=context,
    )
    return StartSessionResponse(session_id=session_id)


@router.post(
    "/message",
    response_model=SendMessageResponse,
)
def send_message(
    payload: SendMessageRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Send one user message to an existing PAWAI chat session.
    Returns PAWAI's (Gemini-generated) reply.
    """
    try:
        reply = chat_svc.send_message(
            session_id=payload.session_id,
            user_id=str(user.id),
            message=payload.message,
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found. Please start a new session.",
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This session belongs to a different user.",
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )
    except Exception as exc:
        # Catch unexpected Gemini / network errors and surface them cleanly.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"PAWAI could not generate a response: {exc}",
        )

    return SendMessageResponse(reply=reply)
