"""
video_stream.py router — AWS DeepLens + Kinesis Video Streams endpoints.

Exposes:
  GET  /video-stream/status          — full pipeline status
  POST /video-stream/create          — create a new Kinesis Video Stream  
  GET  /video-stream/hls/{name}      — get HLS live playback URL
  GET  /video-stream/dash/{name}     — get DASH live playback URL
  GET  /video-stream/streams         — list all streams
  GET  /video-stream/describe/{name} — describe a specific stream
  POST /video-stream/clip/{name}     — extract a clip from stream
  GET  /video-stream/inference/{name}— get DeepLens inference results
  POST /video-stream/analyze/{name}  — start Rekognition stream analysis
"""

import logging
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/video-stream", tags=["Video Stream (DeepLens + Kinesis)"])


# ── Request / Response Models ─────────────────────────────────────────────────

class CreateStreamRequest(BaseModel):
    stream_name: Optional[str] = None

class ClipRequest(BaseModel):
    start_seconds_ago: int = 60
    duration_seconds: int = 30


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/status")
async def pipeline_status():
    """Full status of DeepLens → Kinesis → Rekognition pipeline."""
    try:
        from services.kinesis_video_service import get_video_pipeline_status
        return get_video_pipeline_status()
    except Exception as e:
        logger.error(f"[VideoStream] status error: {e}")
        return {"configured": False, "error": str(e)}


@router.post("/create")
async def create_stream(req: CreateStreamRequest = None):
    """Create a new Kinesis Video Stream."""
    try:
        from services.kinesis_video_service import create_stream as _create
        name = req.stream_name if req else None
        return _create(name)
    except Exception as e:
        logger.error(f"[VideoStream] create error: {e}")
        return {"error": str(e), "status": "ERROR"}


@router.get("/streams")
async def list_all_streams():
    """List all Kinesis Video Streams in the account."""
    try:
        from services.kinesis_video_service import list_streams
        return {"streams": list_streams()}
    except Exception as e:
        logger.error(f"[VideoStream] list error: {e}")
        return {"streams": [], "error": str(e)}


@router.get("/describe/{stream_name}")
async def describe(stream_name: str):
    """Get metadata for a specific stream."""
    try:
        from services.kinesis_video_service import describe_stream
        return describe_stream(stream_name)
    except Exception as e:
        logger.error(f"[VideoStream] describe error: {e}")
        return {"error": str(e), "status": "NOT_FOUND"}


@router.get("/hls/{stream_name}")
async def hls_url(stream_name: str, live: bool = Query(True)):
    """
    Get HLS streaming URL for browser-based live playback.
    
    Use this URL in a <video> element with HLS.js:
    ```js
    const hls = new Hls();
    hls.loadSource(hlsUrl);
    hls.attachMedia(videoElement);
    ```
    """
    try:
        from services.kinesis_video_service import get_hls_streaming_url
        return get_hls_streaming_url(stream_name, live=live)
    except Exception as e:
        logger.error(f"[VideoStream] HLS error: {e}")
        return {"hls_url": "", "error": str(e)}


@router.get("/dash/{stream_name}")
async def dash_url(stream_name: str):
    """Get DASH streaming URL (alternative to HLS)."""
    try:
        from services.kinesis_video_service import get_dash_streaming_url
        return get_dash_streaming_url(stream_name)
    except Exception as e:
        logger.error(f"[VideoStream] DASH error: {e}")
        return {"dash_url": "", "error": str(e)}


@router.get("/inference/{stream_name}")
async def inference_results(stream_name: str):
    """Get DeepLens inference results from the stream."""
    try:
        from services.kinesis_video_service import get_deeplens_inference_results
        return get_deeplens_inference_results(stream_name)
    except Exception as e:
        logger.error(f"[VideoStream] inference error: {e}")
        return {"status": "ERROR", "error": str(e)}


@router.post("/clip/{stream_name}")
async def extract_clip(stream_name: str, req: ClipRequest = None):
    """Extract a video clip from the stream and optionally store to S3."""
    try:
        from services.kinesis_video_service import extract_clip as _extract
        params = req or ClipRequest()
        return _extract(stream_name, params.start_seconds_ago, params.duration_seconds)
    except Exception as e:
        logger.error(f"[VideoStream] clip error: {e}")
        return {"error": str(e), "clip_b64": ""}


@router.post("/analyze/{stream_name}")
async def start_analysis(stream_name: str):
    """Start Rekognition streaming analysis on a Kinesis Video Stream."""
    try:
        from services.kinesis_video_service import analyze_stream_with_rekognition
        return analyze_stream_with_rekognition(stream_name)
    except Exception as e:
        logger.error(f"[VideoStream] analyze error: {e}")
        return {"status": "ERROR", "error": str(e)}
