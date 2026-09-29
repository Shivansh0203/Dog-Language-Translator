"""
PawAI multi-turn chatbot service.

Architecture
------------
* One ``genai.Client`` is created at import time (reuses GEMINI_API_KEY from
  the existing gemini_services module — no second key or client).
* Conversation history is kept **server-side** in a plain Python dict keyed
  by an opaque UUID ``chat_session_id``.  Each entry stores:
    - the authenticated user's id (so one user cannot access another's session)
    - the analysis context (emotion, confidence, Gemini interpretation, …)
    - the full conversation history as a list of
      {"role": "user"|"model", "text": str} dicts
* On every POST /api/chat call we:
    1. Look up the session (or create a new one from the context passed by
       the frontend).
    2. Reconstruct a ``Chat`` object from the stored history so Gemini sees
       the full conversation.
    3. Call chat.send_message() with the new user message.
    4. Append both turns to the stored history.
    5. Return the model reply text.

Why reconstruct instead of keeping the Chat object alive?
  FastAPI workers are stateless; the in-process dict is the persistence layer.
  Reconstructing Chat from history is the documented pattern for stateless
  servers with the google-genai SDK.
"""
from __future__ import annotations

import os
import threading
import uuid
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types

load_dotenv()

# ── Reuse the same client the video-analysis service uses ──────────────────
# We import the module-level client instead of creating a second one.
# If gemini_services raises at import (missing key) we surface the same error.
from app.services.gemini_services import client as _gemini_client, MODEL_NAME

# ── In-process session store ────────────────────────────────────────────────
# key: str (UUID)  →  value: _ChatSession
# Protected by a threading.Lock for correctness under multiple Uvicorn workers
# running in the same process.  For multi-process / multi-server deployments,
# replace this with Redis or a DB table.

_lock = threading.Lock()
_sessions: dict[str, "_ChatSession"] = {}

# Evict sessions older than 2 hours (simple LRU-free approach)
_SESSION_MAX_MESSAGES = 100  # cap per session to avoid unbounded memory


# ── System instruction ───────────────────────────────────────────────────────

def _build_system_instruction(ctx: dict[str, Any]) -> str:
    emotion        = ctx.get("emotion", "unknown")
    confidence_raw = ctx.get("confidence")
    confidence_pct = (
        f"{float(confidence_raw) * 100:.1f}%"
        if confidence_raw is not None
        else "unknown"
    )
    ai_sentence    = (ctx.get("ai_interpretation") or "").strip()
    filename       = (ctx.get("filename") or "a dog video").strip()

    analysis_block = (
        f"Filename: {filename}\n"
        f"Primary emotion detected: {emotion}\n"
        f"Confidence: {confidence_pct}\n"
    )
    if ai_sentence:
        analysis_block += f'AI interpretation: "{ai_sentence}"\n'

    return f"""You are PAWAI, a conversational AI assistant inside the PawAI \
pet-behaviour app.

PawAI's computer-vision model has just analysed the user's dog video and \
produced the following results:

{analysis_block}
Use this analysis as the starting context for the conversation.

Guidelines:
- Answer the user's questions naturally and conversationally.
- Maintain full context across the conversation; remember what was said earlier.
- When discussing the dog's emotional state, never claim scientific certainty.
  Use language such as "appears", "seems", or "may".
- You may explain the detected emotion, what the observed behaviour might \
indicate, possible reasons for the behaviour, what the owner might observe, \
and general ways the owner can respond.
- Do NOT invent observations that were not provided in the analysis above.
- Do NOT repeatedly dump the entire analysis into every response; mention \
details from it only when relevant.
- Keep responses concise, warm, and practical — you are a helpful pet-behaviour \
companion, not a medical authority.
- You are PAWAI, the user's dog-behaviour assistant. Never break character.

ROLE:
- Help users understand their dog's behavior, food, mood, symptoms, training, and daily care.
- Focus only on dogs and dog-related questions.

LANGUAGE:
- Automatically understand the user's language.
- Reply naturally in the same language and style as the user.
- Support English, Hindi, Bengali, Hinglish, Banglish, and mixed-language messages.

RESPONSE STYLE:
- Keep every answer concise, practical, and easy to scan.
- Do NOT write long paragraphs.
- Prefer short bullet points whenever there are multiple reasons, symptoms, causes, steps, warnings, or recommendations.
- Use a maximum of 3-6 bullet points when possible.
- Keep individual bullet points short, normally 1-2 sentences.
- Start with a direct one-line answer when appropriate, followed by relevant bullet points.
- Do not repeat the user's question.
- Do not add unnecessary explanations or filler.
- Do not use emojis.
- Do not use decorative symbols.
- Do not use markdown headings with # characters.
- You may use simple bullet markers such as "•" for clean presentation.

EXAMPLE FORMAT:

If the user asks why their dog is always sleepy, prefer:

"Frequent sleepiness can have several causes:

* Normal rest: Puppies and older dogs naturally sleep more.
* Activity: A very active dog may need more recovery time.
* Weather: Hot weather can make dogs more tired.
* Diet: Poor appetite or dietary changes can affect energy.
* Health issue: Infection, pain, anemia, or other conditions can sometimes cause unusual tiredness.

Contact a veterinarian if the sleepiness is sudden, severe, or accompanied by vomiting, breathing problems, refusal to eat/drink, pain, weakness, or other unusual symptoms."

Do not turn this into one large paragraph.

MEDICAL / SAFETY:
- Do not claim to diagnose a disease.
- Do not present a possible condition as a confirmed diagnosis.
- When symptoms could indicate a medical problem, clearly say that these are possible causes and not a diagnosis.
- For serious, worsening, sudden, or emergency symptoms, recommend contacting a qualified veterinarian.
- Keep medical guidance concise and structured.

CONVERSATION CONTEXT:
- Use the supplied conversation context.
- Remember relevant pet information from the supplied context.
- Treat the CURRENT PET PROFILE as the authoritative profile for the user's dog.
- Use the pet's actual name, breed, age, sex, and species when relevant.
- Never invent or replace stored pet details with another name or profile.
- If the user says "he", "she", "his", or "her", resolve it to the current pet when appropriate.
IMPORTANT:
- Answer the user's actual question directly.
- Do not provide a generic essay.
- Prioritize clarity, concise information, and professional presentation.

"""


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class _ChatSession:
    user_id: str
    context: dict[str, Any]
    history: list[dict[str, str]] = field(default_factory=list)
    # history entries: {"role": "user"|"model", "text": "..."}


# ── Public API ───────────────────────────────────────────────────────────────

def create_session(user_id: str, context: dict[str, Any]) -> str:
    """
    Create a new chat session for this user with the given analysis context.
    Returns a new session_id (opaque UUID string).
    """
    session_id = str(uuid.uuid4())
    with _lock:
        _sessions[session_id] = _ChatSession(
            user_id=str(user_id),
            context=context,
        )
    return session_id


def send_message(
    session_id: str,
    user_id: str,
    message: str,
) -> str:
    """
    Send a user message to the named session and return PAWAI's reply text.

    Raises
    ------
    KeyError    if the session_id does not exist
    PermissionError  if the session belongs to a different user
    RuntimeError    if Gemini returns an empty response
    """
    with _lock:
        session = _sessions.get(session_id)
        if session is None:
            raise KeyError(f"Chat session not found: {session_id}")
        if session.user_id != str(user_id):
            raise PermissionError("Session belongs to a different user.")

    # Build history in the format the SDK expects
    sdk_history: list[genai_types.ContentOrDict] = [
        {"role": turn["role"], "parts": [{"text": turn["text"]}]}
        for turn in session.history
    ]

    system_instruction = _build_system_instruction(session.context)

    # Reconstruct Chat from full history — this is the stateless-server pattern
    chat = _gemini_client.chats.create(
        model=MODEL_NAME,
        config=genai_types.GenerateContentConfig(
            system_instruction=system_instruction,
        ),
        history=sdk_history,
    )

    # Send the new message
    response = chat.send_message(message)

    reply_text = (response.text or "").strip()
    if not reply_text:
        raise RuntimeError("PAWAI returned an empty response. Please try again.")

    # Persist both turns
    with _lock:
        live_session = _sessions.get(session_id)
        if live_session is not None:
            live_session.history.append({"role": "user",  "text": message})
            live_session.history.append({"role": "model", "text": reply_text})
            # Hard cap to avoid unbounded memory
            if len(live_session.history) > _SESSION_MAX_MESSAGES:
                live_session.history = live_session.history[-_SESSION_MAX_MESSAGES:]

    return reply_text


def session_exists(session_id: str, user_id: str) -> bool:
    """Return True iff the session exists and belongs to this user."""
    with _lock:
        s = _sessions.get(session_id)
        return s is not None and s.user_id == str(user_id)


def delete_session(session_id: str) -> None:
    """Remove a session from the store (e.g. on logout)."""
    with _lock:
        _sessions.pop(session_id, None)
