"""
routers/generative_video.py
API endpoints for AWS Generative AI video generation.
Supports text-to-video (Nova Reel), image-to-video (Stability),
and AI scene planning (Titan).
"""
import logging
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/gen-video", tags=["AWS Generative AI Video"])


# ── Request Models ────────────────────────────────────────────────────────────
class TextToVideoRequest(BaseModel):
    prompt: str
    topic: str = "General"
    duration_seconds: int = 6
    camera_motion: str = "static"
    style: str = "educational"
    resolution: str = "1280x720"


class ImageToVideoRequest(BaseModel):
    image_b64: str
    prompt: str = ""
    topic: str = "General"
    motion_strength: float = 0.7


class ScenePlanRequest(BaseModel):
    topic: str
    duration_seconds: int = 30
    num_scenes: int = 5
    style: str = "educational"


# ── Model Info ────────────────────────────────────────────────────────────────

@router.get("/models")
def list_models():
    """List all available generative video models."""
    from services.generative_video_service import list_models
    return list_models()


@router.get("/models/{model_id}")
def model_info(model_id: str):
    """Get details about a specific video generation model."""
    from services.generative_video_service import get_model_info
    return get_model_info(model_id)


# ── Video Generation ──────────────────────────────────────────────────────────

@router.post("/text-to-video")
def text_to_video(req: TextToVideoRequest):
    """Generate video from text using Amazon Nova Reel."""
    from services.generative_video_service import generate_video_from_text
    return generate_video_from_text(
        req.prompt, req.topic, req.duration_seconds,
        req.camera_motion, req.style, req.resolution,
    )


@router.post("/image-to-video")
def image_to_video(req: ImageToVideoRequest):
    """Animate a static image into video using Stability AI."""
    from services.generative_video_service import animate_image
    return animate_image(req.image_b64, req.prompt, req.topic, req.motion_strength)


@router.post("/plan-scenes")
def plan_scenes(req: ScenePlanRequest):
    """Plan a multi-scene educational video storyboard using Amazon Titan."""
    from services.generative_video_service import plan_video_scenes
    return plan_video_scenes(req.topic, req.duration_seconds, req.num_scenes, req.style)


# ── Job Management ────────────────────────────────────────────────────────────

@router.get("/jobs/{job_id}")
def job_status(job_id: str):
    """Check status of a video generation job."""
    from services.generative_video_service import get_job_status
    return get_job_status(job_id)


@router.get("/jobs")
def list_jobs():
    """List all video generation jobs."""
    from services.generative_video_service import list_jobs
    return list_jobs()


@router.get("/status")
def service_status():
    """Check AWS Generative AI Video service status."""
    from services.generative_video_service import get_service_status
    return get_service_status()
