"""
kinesis_video_service.py
AWS DeepLens + Amazon Kinesis Video Streams integration.

Provides:
  1. Stream management — create/describe/list Kinesis Video Streams
  2. Get streaming endpoints — HLS and DASH for live playback in browser
  3. DeepLens integration — read inference results from DeepLens via Kinesis
  4. Video analysis — combine Kinesis stream frames with Rekognition for real-time labeling
  5. Archive management — clip extraction from streams for S3 storage
"""

import base64
import io
import json
import logging
import time
import boto3
from config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    KINESIS_VIDEO_STREAM_NAME,
    KINESIS_DATA_RETENTION,
    S3_BUCKET_NAME,
)

logger = logging.getLogger(__name__)

# ── Boto3 Clients ──────────────────────────────────────────────────────────────
_kvs_client = None
_kvam_client = None  # Kinesis Video Archived Media


def _get_kvs_client():
    """Kinesis Video Streams client — stream management."""
    global _kvs_client
    if _kvs_client is None:
        _kvs_client = boto3.client(
            "kinesisvideo",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
    return _kvs_client


def _get_kvam_client(endpoint_url: str):
    """Kinesis Video Archived Media client — HLS/DASH playback."""
    return boto3.client(
        "kinesis-video-archived-media",
        endpoint_url=endpoint_url,
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )


def _is_configured() -> bool:
    """Check if AWS credentials and stream are configured."""
    return bool(AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY)


# ── Stream Management ─────────────────────────────────────────────────────────

def create_stream(stream_name: str = None) -> dict:
    """
    Create a Kinesis Video Stream (typically receives data from DeepLens).
    Returns stream ARN and creation time.
    """
    name = stream_name or KINESIS_VIDEO_STREAM_NAME
    try:
        kvs = _get_kvs_client()
        resp = kvs.create_stream(
            StreamName=name,
            DataRetentionInHours=KINESIS_DATA_RETENTION,
            MediaType="video/h264",
            Tags={
                "Project": "Saarathi",
                "Source": "DeepLens",
                "Purpose": "AI-Teacher-Video-Analysis",
            },
        )
        logger.info(f"[Kinesis] Created stream: {name} → {resp['StreamARN']}")
        return {
            "stream_name": name,
            "stream_arn": resp["StreamARN"],
            "status": "CREATED",
        }
    except Exception as e:
        if "ResourceInUseException" in str(type(e).__name__):
            logger.info(f"[Kinesis] Stream '{name}' already exists.")
            return describe_stream(name)
        logger.error(f"[Kinesis] create_stream failed: {e}")
        return {"stream_name": name, "error": str(e), "status": "ERROR"}


def describe_stream(stream_name: str = None) -> dict:
    """Get metadata for a Kinesis Video Stream."""
    name = stream_name or KINESIS_VIDEO_STREAM_NAME
    try:
        kvs = _get_kvs_client()
        resp = kvs.describe_stream(StreamName=name)
        info = resp["StreamInfo"]
        return {
            "stream_name": info["StreamName"],
            "stream_arn": info["StreamARN"],
            "status": info["Status"],
            "creation_time": str(info.get("CreationTime", "")),
            "data_retention_hours": info.get("DataRetentionInHours", 0),
            "media_type": info.get("MediaType", ""),
            "kms_key_id": info.get("KmsKeyId", ""),
        }
    except Exception as e:
        logger.warning(f"[Kinesis] describe_stream failed: {e}")
        return {"stream_name": name, "error": str(e), "status": "NOT_FOUND"}


def list_streams() -> list:
    """List all Kinesis Video Streams in the account."""
    try:
        kvs = _get_kvs_client()
        resp = kvs.list_streams(MaxResults=50)
        return [
            {
                "stream_name": s["StreamName"],
                "stream_arn": s["StreamARN"],
                "status": s["Status"],
                "creation_time": str(s.get("CreationTime", "")),
            }
            for s in resp.get("StreamInfoList", [])
        ]
    except Exception as e:
        logger.error(f"[Kinesis] list_streams failed: {e}")
        return []


# ── HLS Streaming (Live Playback in Browser) ──────────────────────────────────

def get_hls_streaming_url(stream_name: str = None, live: bool = True) -> dict:
    """
    Get an HLS streaming URL for browser-based live video playback.
    
    This is how DeepLens video is viewed in the Saarathi frontend:
    DeepLens → Kinesis Video Stream → HLS → <video> element in browser
    
    Parameters:
        stream_name: Kinesis stream name
        live: If True, returns LIVE playback; if False, returns ON_DEMAND
    
    Returns:
        {"hls_url": "...", "expiration": "...", "stream_name": "..."}
    """
    name = stream_name or KINESIS_VIDEO_STREAM_NAME
    try:
        kvs = _get_kvs_client()
        
        # Step 1: Get the data endpoint for HLS
        endpoint_resp = kvs.get_data_endpoint(
            StreamName=name,
            APIName="GET_HLS_STREAMING_SESSION_URL",
        )
        endpoint_url = endpoint_resp["DataEndpoint"]
        
        # Step 2: Get HLS session URL
        kvam = _get_kvam_client(endpoint_url)
        
        playback_mode = "LIVE" if live else "ON_DEMAND"
        params = {
            "StreamName": name,
            "PlaybackMode": playback_mode,
            "HLSFragmentSelector": {
                "FragmentSelectorType": "SERVER_TIMESTAMP" if live else "PRODUCER_TIMESTAMP",
            },
            "ContainerFormat": "FRAGMENTED_MP4",
            "DiscontinuityMode": "ALWAYS",
            "DisplayFragmentTimestamp": "ALWAYS",
            "Expires": 3600,  # URL valid for 1 hour
        }
        
        if not live:
            # For on-demand, specify time range
            params["HLSFragmentSelector"]["TimestampRange"] = {
                "StartTimestamp": time.time() - 3600,  # last hour
                "EndTimestamp": time.time(),
            }
        
        resp = kvam.get_hls_streaming_session_url(**params)
        hls_url = resp["HLSStreamingSessionURL"]
        
        logger.info(f"[Kinesis] HLS URL generated for '{name}' (mode={playback_mode})")
        return {
            "hls_url": hls_url,
            "stream_name": name,
            "playback_mode": playback_mode,
            "expires_in_seconds": 3600,
        }
    
    except Exception as e:
        logger.error(f"[Kinesis] get_hls_url failed: {e}")
        return {
            "hls_url": "",
            "stream_name": name,
            "error": str(e),
        }


def get_dash_streaming_url(stream_name: str = None) -> dict:
    """Get a DASH streaming URL (alternative to HLS for broader browser support)."""
    name = stream_name or KINESIS_VIDEO_STREAM_NAME
    try:
        kvs = _get_kvs_client()
        endpoint_resp = kvs.get_data_endpoint(
            StreamName=name,
            APIName="GET_DASH_STREAMING_SESSION_URL",
        )
        kvam = _get_kvam_client(endpoint_resp["DataEndpoint"])
        
        resp = kvam.get_dash_streaming_session_url(
            StreamName=name,
            PlaybackMode="LIVE",
            DASHFragmentSelector={
                "FragmentSelectorType": "SERVER_TIMESTAMP",
            },
            DisplayFragmentTimestamp="ALWAYS",
            DisplayFragmentNumber="ALWAYS",
            Expires=3600,
        )
        
        logger.info(f"[Kinesis] DASH URL generated for '{name}'")
        return {
            "dash_url": resp["DASHStreamingSessionURL"],
            "stream_name": name,
            "expires_in_seconds": 3600,
        }
    except Exception as e:
        logger.error(f"[Kinesis] get_dash_url failed: {e}")
        return {"dash_url": "", "stream_name": name, "error": str(e)}


# ── DeepLens Inference Integration ────────────────────────────────────────────

def get_deeplens_inference_results(stream_name: str = None) -> dict:
    """
    Read inference results from a DeepLens-connected Kinesis stream.
    
    DeepLens typically sends:
      - Video frames to Kinesis Video Stream
      - Inference results to a separate Kinesis Data Stream or via frame metadata
    
    This function reads the stream metadata for DeepLens inference tags.
    """
    name = stream_name or KINESIS_VIDEO_STREAM_NAME
    try:
        kvs = _get_kvs_client()
        
        # Get media endpoint
        endpoint_resp = kvs.get_data_endpoint(
            StreamName=name,
            APIName="GET_MEDIA",
        )
        
        media_client = boto3.client(
            "kinesis-video-media",
            endpoint_url=endpoint_resp["DataEndpoint"],
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
        
        # Get the latest fragment
        resp = media_client.get_media(
            StreamName=name,
            StartSelector={
                "StartSelectorType": "NOW",
            },
        )
        
        logger.info(f"[Kinesis] DeepLens media stream connected for '{name}'")
        return {
            "stream_name": name,
            "content_type": resp.get("ContentType", "video/h264"),
            "status": "STREAMING",
            "message": "DeepLens inference stream is active. Use HLS URL for browser playback.",
        }
    
    except Exception as e:
        logger.warning(f"[Kinesis] DeepLens inference read failed: {e}")
        return {
            "stream_name": name,
            "status": "UNAVAILABLE",
            "error": str(e),
            "message": "DeepLens stream is not currently active or not configured.",
        }


# ── Video Clip Extraction ─────────────────────────────────────────────────────

def extract_clip(
    stream_name: str = None,
    start_seconds_ago: int = 60,
    duration_seconds: int = 30,
) -> dict:
    """
    Extract a video clip from the Kinesis stream and store it to S3.
    
    Parameters:
        stream_name: Kinesis stream
        start_seconds_ago: How many seconds ago the clip should start
        duration_seconds: Length of clip to extract
    
    Returns:
        {"clip_s3_key": "...", "presigned_url": "...", "duration": ...}
    """
    name = stream_name or KINESIS_VIDEO_STREAM_NAME
    try:
        kvs = _get_kvs_client()
        
        # Get clip endpoint
        endpoint_resp = kvs.get_data_endpoint(
            StreamName=name,
            APIName="GET_CLIP",
        )
        kvam = _get_kvam_client(endpoint_resp["DataEndpoint"])
        
        now = time.time()
        start_ts = now - start_seconds_ago
        end_ts = start_ts + duration_seconds
        
        resp = kvam.get_clip(
            StreamName=name,
            ClipFragmentSelector={
                "FragmentSelectorType": "SERVER_TIMESTAMP",
                "TimestampRange": {
                    "StartTimestamp": start_ts,
                    "EndTimestamp": end_ts,
                },
            },
        )
        
        # Read the MP4 payload
        clip_bytes = resp["Payload"].read()
        clip_b64 = base64.b64encode(clip_bytes).decode()
        
        # Store to S3 if configured
        s3_key = ""
        presigned_url = ""
        if S3_BUCKET_NAME:
            try:
                from services.s3_service import _client as s3_get_client
                s3 = s3_get_client()
                timestamp = int(time.time())
                s3_key = f"clips/{name}/{timestamp}.mp4"
                s3.put_object(
                    Bucket=S3_BUCKET_NAME,
                    Key=s3_key,
                    Body=clip_bytes,
                    ContentType="video/mp4",
                )
                presigned_url = s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": S3_BUCKET_NAME, "Key": s3_key},
                    ExpiresIn=3600,
                )
                logger.info(f"[Kinesis] Clip stored: {s3_key} ({len(clip_bytes)} bytes)")
            except Exception as s3_err:
                logger.warning(f"[Kinesis] S3 clip storage failed: {s3_err}")
        
        return {
            "stream_name": name,
            "clip_b64": clip_b64 if len(clip_b64) < 5_000_000 else "",  # Skip if >5MB
            "clip_size_bytes": len(clip_bytes),
            "s3_key": s3_key,
            "presigned_url": presigned_url,
            "duration_seconds": duration_seconds,
        }
    
    except Exception as e:
        logger.error(f"[Kinesis] extract_clip failed: {e}")
        return {
            "stream_name": name,
            "error": str(e),
            "clip_b64": "",
        }


# ── Stream + Rekognition Analysis ─────────────────────────────────────────────

def analyze_stream_with_rekognition(stream_name: str = None) -> dict:
    """
    Start a Rekognition streaming video analysis session on a Kinesis Video Stream.
    
    This creates a Rekognition Stream Processor that:
      - Reads from the Kinesis Video Stream (DeepLens camera feed)
      - Runs face/object detection in real-time
      - Outputs results to the Kinesis Data Stream
    
    Use Case: Live classroom analysis — detect student engagement, count people, etc.
    """
    name = stream_name or KINESIS_VIDEO_STREAM_NAME
    try:
        rek = boto3.client(
            "rekognition",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
        
        processor_name = f"saarathi-{name}-processor"
        
        # Check if processor already exists
        try:
            status = rek.describe_stream_processor(Name=processor_name)
            return {
                "processor_name": processor_name,
                "status": status.get("Status", "UNKNOWN"),
                "stream_name": name,
                "message": "Stream processor already exists.",
            }
        except Exception:
            pass  # Doesn't exist, create it
        
        # Create the stream processor
        resp = rek.create_stream_processor(
            Input={
                "KinesisVideoStream": {
                    "Arn": describe_stream(name).get("stream_arn", ""),
                },
            },
            Output={
                "KinesisDataStream": {
                    "Arn": "",  # Set your output Kinesis Data Stream ARN here
                },
            },
            Name=processor_name,
            Settings={
                "FaceSearch": {
                    "CollectionId": "saarathi-faces",
                    "FaceMatchThreshold": 70.0,
                },
            },
            RoleArn="",  # Set your IAM role ARN for Rekognition
        )
        
        logger.info(f"[Kinesis+Rek] Stream processor created: {processor_name}")
        return {
            "processor_name": processor_name,
            "processor_arn": resp.get("StreamProcessorArn", ""),
            "stream_name": name,
            "status": "CREATED",
        }
    
    except Exception as e:
        logger.error(f"[Kinesis+Rek] analyze_stream failed: {e}")
        return {
            "stream_name": name,
            "error": str(e),
            "status": "ERROR",
        }


# ── Status Summary ────────────────────────────────────────────────────────────

def get_video_pipeline_status() -> dict:
    """
    Full status of the DeepLens → Kinesis → Rekognition pipeline.
    """
    return {
        "configured": _is_configured(),
        "default_stream": KINESIS_VIDEO_STREAM_NAME,
        "data_retention_hours": KINESIS_DATA_RETENTION,
        "stream_info": describe_stream(),
        "streams": list_streams(),
    }
