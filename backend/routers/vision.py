"""
routers/vision.py
Endpoints for computer-vision-powered image and video generation.
"""
import logging
from fastapi import APIRouter, HTTPException
from models import ImageRequest, ImageResponse, VideoRequest, VideoResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vision", tags=["Vision"])


@router.post("/generate-image", response_model=ImageResponse)
async def generate_image_endpoint(req: ImageRequest):
    """
    Generate a 512x512 educational image from a visual_scene description.
    Uses Bedrock Titan Image Generator v1, falls back to Pillow placeholder.
    """
    try:
        from services.image_service import generate_image
        result = generate_image(req.prompt, width=512, height=512)

        # ── Store to S3 (fire-and-forget) ─────────────────────────────────
        try:
            from services.s3_service import store_image
            store_image(req.prompt[:60], result["image_b64"])
        except Exception as s3_err:
            logger.warning(f"[S3] image storage failed (non-fatal): {s3_err}")

        return ImageResponse(
            image_b64=result["image_b64"],
            prompt=result["prompt"],
            source=result.get("source", "unknown"),
        )
    except Exception as e:
        logger.error(f"/vision/generate-image error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-video", response_model=VideoResponse)
async def generate_video_endpoint(req: VideoRequest):
    """
    Assemble a ~7s educational MP4 slideshow from a topic image + caption.
    Returns base64-encoded MP4.
    """
    try:
        from services.video_service import generate_video
        result = generate_video(
            image_b64=req.image_b64,
            topic=req.topic,
            spoken_text=req.spoken_text,
        )

        # ── Store to S3 (fire-and-forget) ─────────────────────────────────
        try:
            from services.s3_service import store_video
            store_video(req.topic, result.get("video_b64", ""))
        except Exception as s3_err:
            logger.warning(f"[S3] video storage failed (non-fatal): {s3_err}")

        return VideoResponse(
            video_b64=result.get("video_b64", ""),
            topic=result.get("topic", req.topic),
        )
    except Exception as e:
        logger.error(f"/vision/generate-video error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

