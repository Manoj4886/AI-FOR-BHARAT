"""
routers/nova_reel.py
Amazon Nova Reel API endpoints for AI-powered video generation.
"""
import logging
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/nova-reel", tags=["Amazon Nova Reel"])


# ── Request Models ────────────────────────────────────────────────────────────
class GenerateVideoRequest(BaseModel):
    prompt: str
    topic: str = ""
    camera_motion: str = "static"
    style: str = "educational"
    duration: int = 6
    seed: int = 0


class StoryboardRequest(BaseModel):
    topic: str
    num_shots: int = 4
    style: str = "educational"


# ── Video Generation ──────────────────────────────────────────────────────────

@router.post("/generate")
def generate(req: GenerateVideoRequest):
    """Generate an educational video clip using Amazon Nova Reel."""
    from services.nova_reel_service import generate_video
    return generate_video(req.prompt, req.topic, req.camera_motion, req.style, req.duration, req.seed)


@router.post("/storyboard")
def storyboard(req: StoryboardRequest):
    """Create a multi-shot video storyboard for a topic."""
    from services.nova_reel_service import generate_storyboard
    return generate_storyboard(req.topic, req.num_shots, req.style)


# ── Camera & Styles ───────────────────────────────────────────────────────────

@router.get("/camera-motions")
def camera_motions():
    """List all 11 camera motion presets."""
    from services.nova_reel_service import list_camera_motions
    return list_camera_motions()


@router.get("/styles")
def styles():
    """List all educational style presets."""
    from services.nova_reel_service import list_styles
    return list_styles()


# ── Jobs ──────────────────────────────────────────────────────────────────────

@router.get("/jobs/{job_id}")
def job_status(job_id: str):
    """Check status of a Nova Reel video generation job."""
    from services.nova_reel_service import get_job
    return get_job(job_id)


@router.get("/jobs")
def jobs():
    """List all Nova Reel video generation jobs."""
    from services.nova_reel_service import list_jobs
    return list_jobs()


@router.get("/status")
def status():
    """Check Amazon Nova Reel service status."""
    from services.nova_reel_service import get_status
    return get_status()
