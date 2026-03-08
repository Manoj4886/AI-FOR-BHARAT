"""
routers/conversation.py
API endpoints for Conversational AI — multi-turn context,
voice settings, and session management.
"""
import logging
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/conversation", tags=["Conversational AI"])


# ── Request Models ────────────────────────────────────────────────────────────
class VoiceSettingsRequest(BaseModel):
    session_id: str
    voice_enabled: bool = True
    voice_speed: float = 1.0
    voice_name: str = "auto"
    language: str = "en"


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.get("/history/{session_id}")
def get_history(session_id: str):
    """Get the full conversation history for a session."""
    from services.conversation_service import get_conversation
    return get_conversation(session_id)


@router.delete("/clear/{session_id}")
def clear_history(session_id: str):
    """Clear conversation history (fresh start)."""
    from services.conversation_service import clear_conversation
    return clear_conversation(session_id)


@router.post("/voice-settings")
def update_voice(req: VoiceSettingsRequest):
    """Update voice/speech settings for a session."""
    from services.conversation_service import update_settings
    return update_settings(req.session_id, {
        "voice_enabled": req.voice_enabled,
        "voice_speed": req.voice_speed,
        "voice_name": req.voice_name,
        "language": req.language,
    })


@router.get("/sessions")
def list_sessions():
    """List all active conversation sessions."""
    from services.conversation_service import get_all_sessions
    return get_all_sessions()


@router.get("/status")
def conversation_status():
    """Check Conversational AI status."""
    from services.conversation_service import _conversations
    return {
        "status": "active",
        "provider": "conversational-ai",
        "active_sessions": len(_conversations),
        "features": [
            "multi_turn_context",
            "conversation_memory",
            "context_summarization",
            "voice_settings",
            "session_management",
            "speech_synthesis",
        ],
    }
