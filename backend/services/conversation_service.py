"""
services/conversation_service.py
Conversational AI service — maintains per-session multi-turn context
so follow-up questions are natural and context-aware.

Features:
  - Per-session conversation memory (sliding window)
  - Context-aware prompt building for LLM
  - Conversation summarization for long sessions
  - Voice/speech settings per session
  - Conversation export and management
"""
import logging
import time
from collections import defaultdict

logger = logging.getLogger(__name__)

# ── In-memory conversation store ──────────────────────────────────────────────
# {session_id: { "messages": [...], "created": ..., "settings": {...} }}
_conversations: dict[str, dict] = defaultdict(lambda: {
    "messages": [],
    "created": time.time(),
    "last_active": time.time(),
    "settings": {
        "voice_enabled": True,
        "voice_speed": 1.0,
        "voice_name": "auto",
        "skill_level": "advanced",
        "language": "en",
    },
    "summary": "",
    "turn_count": 0,
})

MAX_CONTEXT_TURNS = 10  # Keep last 10 Q&A pairs in context window


def add_message(session_id: str, role: str, content: str, metadata: dict | None = None) -> dict:
    """
    Add a message to the conversation history.
    role: 'user' or 'assistant'
    """
    conv = _conversations[session_id]
    msg = {
        "role": role,
        "content": content,
        "timestamp": time.time(),
        "metadata": metadata or {},
    }
    conv["messages"].append(msg)
    conv["last_active"] = time.time()
    if role == "user":
        conv["turn_count"] += 1

    # Trim old messages beyond the context window (keep system-level summary)
    if len(conv["messages"]) > MAX_CONTEXT_TURNS * 2:
        _summarize_old_messages(session_id)

    return {"status": "added", "total_messages": len(conv["messages"])}


def get_context_messages(session_id: str) -> list[dict]:
    """
    Get the conversation history formatted for LLM input.
    Returns list of {"role": "user"|"assistant", "content": "..."}
    """
    conv = _conversations[session_id]
    messages = []

    # If there's a summary of older messages, prepend it
    if conv["summary"]:
        messages.append({
            "role": "user",
            "content": f"[Previous conversation summary: {conv['summary']}]",
        })
        messages.append({
            "role": "assistant",
            "content": "I remember our previous discussion. Let me continue from where we left off.",
        })

    # Add recent messages (within context window)
    recent = conv["messages"][-(MAX_CONTEXT_TURNS * 2):]
    for msg in recent:
        messages.append({
            "role": msg["role"],
            "content": msg["content"],
        })

    return messages


def build_conversational_prompt(session_id: str, new_question: str) -> list[dict]:
    """
    Build the full message list for the LLM, including conversation
    history + the new question. This is what gets sent to Groq.
    """
    context = get_context_messages(session_id)

    # Add the new question
    context.append({
        "role": "user",
        "content": new_question,
    })

    return context


def get_conversation(session_id: str) -> dict:
    """Get the full conversation state for a session."""
    conv = _conversations[session_id]
    return {
        "session_id": session_id,
        "messages": [
            {
                "role": m["role"],
                "content": m["content"][:200] + "..." if len(m["content"]) > 200 else m["content"],
                "timestamp": m["timestamp"],
            }
            for m in conv["messages"]
        ],
        "turn_count": conv["turn_count"],
        "created": conv["created"],
        "last_active": conv["last_active"],
        "settings": conv["settings"],
        "summary": conv["summary"],
    }


def update_settings(session_id: str, settings: dict) -> dict:
    """Update voice/speech settings for a session."""
    conv = _conversations[session_id]
    conv["settings"].update(settings)
    return {"status": "updated", "settings": conv["settings"]}


def clear_conversation(session_id: str) -> dict:
    """Clear conversation history for a session (fresh start)."""
    if session_id in _conversations:
        turn_count = _conversations[session_id]["turn_count"]
        _conversations[session_id] = {
            "messages": [],
            "created": time.time(),
            "last_active": time.time(),
            "settings": _conversations[session_id].get("settings", {}),
            "summary": "",
            "turn_count": 0,
        }
        return {"status": "cleared", "previous_turns": turn_count}
    return {"status": "no_conversation_found"}


def get_all_sessions() -> dict:
    """List all active conversation sessions."""
    sessions = []
    for sid, conv in _conversations.items():
        sessions.append({
            "session_id": sid,
            "turn_count": conv["turn_count"],
            "last_active": conv["last_active"],
            "message_count": len(conv["messages"]),
        })
    sessions.sort(key=lambda s: s["last_active"], reverse=True)
    return {"sessions": sessions, "total": len(sessions)}


def _summarize_old_messages(session_id: str):
    """
    Summarize older messages to keep context window small.
    Keeps the last MAX_CONTEXT_TURNS*2 messages, summarizes the rest.
    """
    conv = _conversations[session_id]
    old = conv["messages"][:-(MAX_CONTEXT_TURNS * 2)]
    if not old:
        return

    # Build a simple summary from old messages
    topics = set()
    for msg in old:
        if msg["role"] == "user" and len(msg["content"]) > 5:
            topics.add(msg["content"][:80])

    summary_parts = []
    if conv["summary"]:
        summary_parts.append(conv["summary"])
    summary_parts.append(f"Earlier questions: {', '.join(list(topics)[:5])}")

    conv["summary"] = ". ".join(summary_parts)[:500]
    conv["messages"] = conv["messages"][-(MAX_CONTEXT_TURNS * 2):]
    logger.info(f"Summarized {len(old)} old messages for session {session_id}")
