"""
routers/avatar_engines.py
API endpoints for avatar engine management — Unity, Unreal Engine, Three.js.
Supports avatar creation, animation, lip-sync, expressions, gestures,
gaze tracking, and render settings.
"""
import logging
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/avatars", tags=["Avatar Engines (Unity / Unreal / Three.js)"])


# ── Request Models ────────────────────────────────────────────────────────────
class CreateAvatarRequest(BaseModel):
    session_id: str
    engine: str  # "unity" | "unreal" | "threejs"
    avatar_url: str = ""
    settings: dict | None = None


class AnimationRequest(BaseModel):
    session_id: str
    state: str  # "idle", "talking", "explaining", "pointing", etc.
    blend_time: float = 0.3


class ExpressionRequest(BaseModel):
    session_id: str
    expression: str  # "happy", "sad", "surprised", "thinking", "neutral"
    intensity: float = 1.0


class VisemeRequest(BaseModel):
    session_id: str
    viseme: str  # "sil", "aa", "E", "I", "O", "U", etc.


class EyeTargetRequest(BaseModel):
    session_id: str
    x: float = 0.0
    y: float = 0.0
    z: float = 1.0


class HeadRotationRequest(BaseModel):
    session_id: str
    pitch: float = 0.0
    yaw: float = 0.0
    roll: float = 0.0


class GestureRequest(BaseModel):
    session_id: str
    gesture: str  # "wave", "point_board", "thumbs_up", "thinking", etc.


class RenderSettingsRequest(BaseModel):
    session_id: str
    quality: str = "high"
    shadows: bool = True
    anti_aliasing: bool = True
    fps_target: int = 60
    resolution_scale: float = 1.0


# ── Engine Info Endpoints ─────────────────────────────────────────────────────

@router.get("/engines")
def list_engines():
    """List all supported avatar engines (Unity, Unreal, Three.js)."""
    from services.avatar_engine_service import list_engines
    return list_engines()


@router.get("/engines/{engine}")
def engine_info(engine: str):
    """Get detailed info about a specific engine."""
    from services.avatar_engine_service import get_engine_info
    return get_engine_info(engine)


# ── Avatar Session Endpoints ──────────────────────────────────────────────────

@router.post("/create")
def create_avatar(req: CreateAvatarRequest):
    """Create an avatar session with a specific engine."""
    from services.avatar_engine_service import create_avatar
    return create_avatar(req.session_id, req.engine, req.avatar_url, req.settings)


@router.get("/state/{session_id}")
def avatar_state(session_id: str):
    """Get current avatar state (animation, expression, lip-sync, gaze)."""
    from services.avatar_engine_service import get_avatar_state
    return get_avatar_state(session_id)


# ── Animation & Expression ────────────────────────────────────────────────────

@router.post("/animate")
def set_animation(req: AnimationRequest):
    """Set animation state (idle, talking, explaining, pointing, etc.)."""
    from services.avatar_engine_service import set_animation
    return set_animation(req.session_id, req.state, req.blend_time)


@router.post("/expression")
def set_expression(req: ExpressionRequest):
    """Set facial expression (happy, sad, surprised, thinking, neutral)."""
    from services.avatar_engine_service import set_expression
    return set_expression(req.session_id, req.expression, req.intensity)


# ── Lip Sync ──────────────────────────────────────────────────────────────────

@router.post("/viseme")
def set_viseme(req: VisemeRequest):
    """Set current viseme for lip-sync."""
    from services.avatar_engine_service import set_viseme
    return set_viseme(req.session_id, req.viseme)


@router.get("/viseme-map")
def viseme_map():
    """Get the full viseme mapping for all engines."""
    from services.avatar_engine_service import get_viseme_map
    return get_viseme_map()


# ── Gaze & Head Tracking ─────────────────────────────────────────────────────

@router.post("/eye-target")
def set_eye_target(req: EyeTargetRequest):
    """Set eye gaze target in 3D space."""
    from services.avatar_engine_service import set_eye_target
    return set_eye_target(req.session_id, req.x, req.y, req.z)


@router.post("/head-rotation")
def set_head_rotation(req: HeadRotationRequest):
    """Set head rotation angles (pitch, yaw, roll)."""
    from services.avatar_engine_service import set_head_rotation
    return set_head_rotation(req.session_id, req.pitch, req.yaw, req.roll)


# ── Gestures ──────────────────────────────────────────────────────────────────

@router.post("/gesture")
def set_gesture(req: GestureRequest):
    """Trigger a body gesture (wave, point, thumbs_up, thinking, etc.)."""
    from services.avatar_engine_service import set_gesture
    return set_gesture(req.session_id, req.gesture)


@router.get("/gestures")
def list_gestures():
    """List all available gestures."""
    from services.avatar_engine_service import list_gestures
    return list_gestures()


# ── Render Settings ───────────────────────────────────────────────────────────

@router.post("/render-settings")
def update_render(req: RenderSettingsRequest):
    """Update avatar render quality settings."""
    from services.avatar_engine_service import update_render_settings
    return update_render_settings(req.session_id, {
        "quality": req.quality,
        "shadows": req.shadows,
        "anti_aliasing": req.anti_aliasing,
        "fps_target": req.fps_target,
        "resolution_scale": req.resolution_scale,
    })


# ── Sessions ──────────────────────────────────────────────────────────────────

@router.get("/sessions")
def list_sessions():
    """List all active avatar sessions."""
    from services.avatar_engine_service import list_avatar_sessions
    return list_avatar_sessions()


@router.get("/status")
def avatar_status():
    """Check Avatar Engines status."""
    from services.avatar_engine_service import list_engines as _list
    engines = _list()
    return {
        "status": "active",
        "engines": [e["name"] for e in engines["engines"]],
        "total_engines": engines["total"],
        "features": [
            "unity_interactive_avatars",
            "unreal_metahuman",
            "threejs_web_avatars",
            "lip_sync",
            "facial_expressions",
            "gesture_system",
            "gaze_tracking",
            "head_rotation",
            "render_quality_control",
        ],
    }
