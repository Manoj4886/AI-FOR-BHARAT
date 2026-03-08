"""
routers/mediaconvert.py
AWS Elemental MediaConvert API endpoints for video transcoding and processing.
"""
import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mediaconvert", tags=["AWS Elemental MediaConvert"])


# ── Request Models ────────────────────────────────────────────────────────────
class TranscodeRequest(BaseModel):
    input_s3_uri: str
    output_format: str = "mp4"
    resolution: str = "1080p"
    audio_preset: str = "narration"
    caption_file: str = ""
    caption_format: str = "srt"
    watermark_text: str = ""
    thumbnail: bool = True


class AdaptiveStreamRequest(BaseModel):
    input_s3_uri: str
    stream_type: str = "hls"
    resolutions: Optional[List[str]] = None


class ThumbnailRequest(BaseModel):
    input_s3_uri: str
    interval_seconds: int = 5
    width: int = 320
    height: int = 180
    format: str = "jpg"


class CaptionRequest(BaseModel):
    input_s3_uri: str
    caption_s3_uri: str
    caption_format: str = "srt"
    language: str = "en"


# ── Transcoding ───────────────────────────────────────────────────────────────

@router.post("/transcode")
def transcode(req: TranscodeRequest):
    """Transcode video to optimized format with resolution, audio, and caption options."""
    from services.mediaconvert_service import create_transcode_job
    return create_transcode_job(
        req.input_s3_uri, req.output_format, req.resolution,
        req.audio_preset, req.caption_file, req.caption_format,
        req.watermark_text, req.thumbnail,
    )


@router.post("/adaptive-stream")
def adaptive_stream(req: AdaptiveStreamRequest):
    """Create adaptive bitrate streaming outputs (HLS/DASH) with multiple resolutions."""
    from services.mediaconvert_service import create_adaptive_stream
    return create_adaptive_stream(req.input_s3_uri, req.stream_type, req.resolutions)


@router.post("/thumbnails")
def thumbnails(req: ThumbnailRequest):
    """Generate thumbnail images from video at specified intervals."""
    from services.mediaconvert_service import generate_thumbnails
    return generate_thumbnails(req.input_s3_uri, req.interval_seconds, req.width, req.height, req.format)


@router.post("/captions")
def captions(req: CaptionRequest):
    """Embed captions/subtitles into a video."""
    from services.mediaconvert_service import add_captions
    return add_captions(req.input_s3_uri, req.caption_s3_uri, req.caption_format, req.language)


# ── Presets ───────────────────────────────────────────────────────────────────

@router.get("/formats")
def formats():
    """List available output video formats."""
    from services.mediaconvert_service import list_output_formats
    return list_output_formats()


@router.get("/resolutions")
def resolutions():
    """List available resolution presets (480p to 4K)."""
    from services.mediaconvert_service import list_resolutions
    return list_resolutions()


@router.get("/audio-presets")
def audio_presets():
    """List available audio presets."""
    from services.mediaconvert_service import list_audio_presets
    return list_audio_presets()


@router.get("/caption-formats")
def caption_formats():
    """List supported caption/subtitle formats."""
    from services.mediaconvert_service import list_caption_formats
    return list_caption_formats()


# ── Jobs ──────────────────────────────────────────────────────────────────────

@router.get("/jobs/{job_id}")
def job_status(job_id: str):
    """Check status of a MediaConvert job."""
    from services.mediaconvert_service import get_job
    return get_job(job_id)


@router.get("/jobs")
def jobs():
    """List all MediaConvert jobs."""
    from services.mediaconvert_service import list_jobs
    return list_jobs()


@router.get("/status")
def status():
    """Check AWS Elemental MediaConvert service status."""
    from services.mediaconvert_service import get_status
    return get_status()
