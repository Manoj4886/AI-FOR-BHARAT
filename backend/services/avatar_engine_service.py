"""
services/avatar_engine_service.py
Unified Avatar Engine management service supporting:
  - Unity (interactive 3D avatars with real-time physics/animation)
  - Unreal Engine (ultra-realistic MetaHuman avatars)
  - Three.js (lightweight web-based 3D avatars)

Each engine manages avatar configuration, animation state,
lip-sync parameters, and rendering settings.
"""
import logging
import time
from collections import defaultdict

logger = logging.getLogger(__name__)

# ── Engine Configurations ─────────────────────────────────────────────────────
ENGINES = {
    "unity": {
        "name": "Unity",
        "version": "2023.3 LTS",
        "description": "Interactive 3D avatars with real-time physics, animation blending, and gesture recognition",
        "features": [
            "real_time_animation",
            "physics_simulation",
            "animation_blending",
            "gesture_recognition",
            "facial_mocap",
            "interactive_props",
            "particle_effects",
            "spatial_audio",
        ],
        "supported_formats": ["FBX", "GLTF", "GLB", "USD", "VRM"],
        "render_pipeline": "URP (Universal Render Pipeline)",
        "max_bones": 300,
        "blend_shapes": 52,
        "streaming_protocol": "WebRTC",
    },
    "unreal": {
        "name": "Unreal Engine",
        "version": "5.4",
        "description": "Ultra-realistic MetaHuman avatars with cinematic-quality rendering and Lumen GI",
        "features": [
            "metahuman_integration",
            "lumen_global_illumination",
            "nanite_mesh",
            "hair_simulation",
            "cloth_simulation",
            "subsurface_scattering",
            "ray_tracing",
            "pixel_streaming",
            "live_link_face",
            "control_rig",
        ],
        "supported_formats": ["FBX", "USD", "ABC", "MetaHuman"],
        "render_pipeline": "Nanite + Lumen",
        "max_bones": 500,
        "blend_shapes": 120,
        "streaming_protocol": "Pixel Streaming",
    },
    "threejs": {
        "name": "Three.js",
        "version": "r168",
        "description": "Lightweight web-based 3D avatars with browser-native rendering using WebGL/WebGPU",
        "features": [
            "webgl_rendering",
            "webgpu_support",
            "ready_player_me",
            "vrm_support",
            "morph_targets",
            "skeletal_animation",
            "pbr_materials",
            "environment_mapping",
            "shadow_maps",
            "post_processing",
        ],
        "supported_formats": ["GLTF", "GLB", "VRM", "FBX (via converter)"],
        "render_pipeline": "WebGL 2.0 / WebGPU",
        "max_bones": 128,
        "blend_shapes": 52,
        "streaming_protocol": "Direct (in-browser)",
    },
}

# ── Per-session avatar state ─────────────────────────────────────────────────
_avatar_sessions = {}


def _default_session(engine: str) -> dict:
    return {
        "engine": engine,
        "avatar_url": "",
        "animation_state": "idle",
        "expression": "neutral",
        "lip_sync_active": False,
        "viseme": "sil",
        "eye_target": {"x": 0.0, "y": 0.0, "z": 1.0},
        "head_rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
        "body_gesture": "none",
        "created": time.time(),
        "last_updated": time.time(),
        "settings": {
            "quality": "high",
            "shadows": True,
            "anti_aliasing": True,
            "fps_target": 60,
            "resolution_scale": 1.0,
        },
    }


# ── Engine Info ──────────────────────────────────────────────────────────────

def get_engine_info(engine: str) -> dict:
    """Get info about a specific avatar engine."""
    if engine not in ENGINES:
        return {"error": f"Unknown engine: {engine}. Available: {list(ENGINES.keys())}"}
    return {"engine": engine, **ENGINES[engine]}


def list_engines() -> dict:
    """List all supported avatar engines with comparison."""
    engines = []
    for key, cfg in ENGINES.items():
        engines.append({
            "id": key,
            "name": cfg["name"],
            "version": cfg["version"],
            "description": cfg["description"],
            "feature_count": len(cfg["features"]),
            "max_blend_shapes": cfg["blend_shapes"],
            "render_pipeline": cfg["render_pipeline"],
            "streaming": cfg["streaming_protocol"],
        })
    return {"engines": engines, "total": len(engines)}


# ── Avatar Session Management ────────────────────────────────────────────────

def create_avatar(session_id: str, engine: str, avatar_url: str = "", settings: dict | None = None) -> dict:
    """Create/configure an avatar session for a specific engine."""
    if engine not in ENGINES:
        return {"error": f"Unknown engine: {engine}"}

    session = _default_session(engine)
    if avatar_url:
        session["avatar_url"] = avatar_url
    if settings:
        session["settings"].update(settings)

    _avatar_sessions[session_id] = session
    return {
        "status": "created",
        "session_id": session_id,
        "engine": engine,
        "engine_name": ENGINES[engine]["name"],
        "features": ENGINES[engine]["features"],
        "avatar_url": session["avatar_url"],
    }


def get_avatar_state(session_id: str) -> dict:
    """Get current avatar state for a session."""
    if session_id not in _avatar_sessions:
        return {"status": "no_session", "session_id": session_id}
    session = _avatar_sessions[session_id]
    return {
        "session_id": session_id,
        "engine": session["engine"],
        "engine_name": ENGINES[session["engine"]]["name"],
        "animation_state": session["animation_state"],
        "expression": session["expression"],
        "lip_sync_active": session["lip_sync_active"],
        "viseme": session["viseme"],
        "eye_target": session["eye_target"],
        "head_rotation": session["head_rotation"],
        "body_gesture": session["body_gesture"],
        "settings": session["settings"],
    }


# ── Animation Control ────────────────────────────────────────────────────────

def set_animation(session_id: str, state: str, blend_time: float = 0.3) -> dict:
    """Set avatar animation state (idle, talking, explaining, pointing, etc.)."""
    if session_id not in _avatar_sessions:
        _avatar_sessions[session_id] = _default_session("threejs")

    session = _avatar_sessions[session_id]
    prev_state = session["animation_state"]
    session["animation_state"] = state
    session["last_updated"] = time.time()

    return {
        "status": "animation_set",
        "previous": prev_state,
        "current": state,
        "blend_time": blend_time,
        "engine": session["engine"],
    }


def set_expression(session_id: str, expression: str, intensity: float = 1.0) -> dict:
    """Set facial expression (happy, sad, surprised, thinking, neutral, etc.)."""
    if session_id not in _avatar_sessions:
        _avatar_sessions[session_id] = _default_session("threejs")

    session = _avatar_sessions[session_id]
    prev_expression = session["expression"]
    session["expression"] = expression
    session["last_updated"] = time.time()

    return {
        "status": "expression_set",
        "previous": prev_expression,
        "current": expression,
        "intensity": intensity,
        "engine": session["engine"],
    }


# ── Lip Sync ─────────────────────────────────────────────────────────────────

VISEME_MAP = {
    "sil": "silence",
    "aa": "open_jaw",
    "E": "smile_open",
    "I": "narrow",
    "O": "round",
    "U": "tight_round",
    "FF": "lower_lip_bite",
    "TH": "tongue_between_teeth",
    "DD": "tongue_behind_teeth",
    "kk": "back_tongue",
    "CH": "teeth_together",
    "SS": "narrow_teeth",
    "nn": "tongue_up",
    "RR": "rounded",
    "PP": "lips_closed",
}


def set_viseme(session_id: str, viseme: str) -> dict:
    """Set current viseme for lip-sync across all engines."""
    if session_id not in _avatar_sessions:
        _avatar_sessions[session_id] = _default_session("threejs")

    session = _avatar_sessions[session_id]
    session["viseme"] = viseme
    session["lip_sync_active"] = viseme != "sil"
    session["last_updated"] = time.time()

    return {
        "viseme": viseme,
        "description": VISEME_MAP.get(viseme, "unknown"),
        "lip_sync_active": session["lip_sync_active"],
        "engine": session["engine"],
    }


def get_viseme_map() -> dict:
    """Get the full viseme mapping (for frontend rendering)."""
    return {
        "visemes": VISEME_MAP,
        "total": len(VISEME_MAP),
        "supported_engines": list(ENGINES.keys()),
    }


# ── Gaze & Head Tracking ────────────────────────────────────────────────────

def set_eye_target(session_id: str, x: float, y: float, z: float) -> dict:
    """Set eye gaze target position in 3D space."""
    if session_id not in _avatar_sessions:
        _avatar_sessions[session_id] = _default_session("threejs")

    session = _avatar_sessions[session_id]
    session["eye_target"] = {"x": x, "y": y, "z": z}
    session["last_updated"] = time.time()

    return {"status": "eye_target_set", "target": session["eye_target"], "engine": session["engine"]}


def set_head_rotation(session_id: str, pitch: float, yaw: float, roll: float) -> dict:
    """Set head rotation (degrees) for look-at behavior."""
    if session_id not in _avatar_sessions:
        _avatar_sessions[session_id] = _default_session("threejs")

    session = _avatar_sessions[session_id]
    session["head_rotation"] = {"pitch": pitch, "yaw": yaw, "roll": roll}
    session["last_updated"] = time.time()

    return {"status": "head_rotation_set", "rotation": session["head_rotation"], "engine": session["engine"]}


# ── Gesture System ───────────────────────────────────────────────────────────

GESTURES = {
    "none": "No gesture",
    "wave": "Friendly wave",
    "point_board": "Point at the board",
    "thumbs_up": "Thumbs up approval",
    "thinking": "Hand on chin, thinking",
    "open_arms": "Open arms welcome",
    "writing": "Writing on board",
    "clap": "Clapping hands",
    "raise_hand": "Raise hand for attention",
    "head_tilt": "Curious head tilt",
    "shrug": "Shoulder shrug",
    "count_fingers": "Counting on fingers",
}


def set_gesture(session_id: str, gesture: str) -> dict:
    """Trigger a body gesture animation."""
    if session_id not in _avatar_sessions:
        _avatar_sessions[session_id] = _default_session("threejs")

    session = _avatar_sessions[session_id]
    session["body_gesture"] = gesture
    session["last_updated"] = time.time()

    return {
        "status": "gesture_set",
        "gesture": gesture,
        "description": GESTURES.get(gesture, "custom"),
        "engine": session["engine"],
    }


def list_gestures() -> dict:
    """Get all available gestures."""
    return {"gestures": GESTURES, "total": len(GESTURES)}


# ── Render Settings ──────────────────────────────────────────────────────────

def update_render_settings(session_id: str, settings: dict) -> dict:
    """Update rendering quality settings for the avatar."""
    if session_id not in _avatar_sessions:
        _avatar_sessions[session_id] = _default_session("threejs")

    session = _avatar_sessions[session_id]
    session["settings"].update(settings)
    session["last_updated"] = time.time()

    return {"status": "settings_updated", "settings": session["settings"], "engine": session["engine"]}


# ── Active Sessions ──────────────────────────────────────────────────────────

def list_avatar_sessions() -> dict:
    """List all active avatar sessions."""
    sessions = []
    for sid, s in _avatar_sessions.items():
        sessions.append({
            "session_id": sid,
            "engine": s["engine"],
            "animation_state": s["animation_state"],
            "expression": s["expression"],
            "lip_sync_active": s["lip_sync_active"],
            "last_updated": s["last_updated"],
        })
    sessions.sort(key=lambda x: x["last_updated"], reverse=True)
    return {"sessions": sessions, "total": len(sessions)}
