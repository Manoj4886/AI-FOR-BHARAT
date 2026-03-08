"""
services/s3_service.py
──────────────────────
AWS S3 storage helper for the AI Teacher backend.

All public functions are graceful: if S3_BUCKET_NAME is not configured
or any AWS call fails, they log a warning and return a safe default.
This means the rest of the app never crashes due to S3 issues.

Key layout in the bucket:
  sessions/{user_id}/{timestamp}.json   ← Q&A logs (one per /ask call)
  quiz/{user_id}/{timestamp}.json       ← Quiz results
  progress/{user_id}/latest.json        ← Progress snapshot
  audio/{topic_slug}/{timestamp}.mp3    ← Polly MP3 audio
  images/{topic_slug}/{timestamp}.png   ← Generated images
  videos/{topic_slug}/{timestamp}.mp4   ← Generated videos
  uploads/{user_id}/{timestamp}_{name}  ← User-uploaded files
"""

import base64
import io
import json
import logging
import re
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError

from config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    S3_BUCKET_NAME,
)

logger = logging.getLogger(__name__)

# ─── S3 client (lazy singleton) ───────────────────────────────────────────────

_s3_client = None
_bucket_ensured = False


def _get_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
    return _s3_client


def _is_configured() -> bool:
    return bool(S3_BUCKET_NAME and AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY)


def _ensure_bucket():
    """Create the S3 bucket if it doesn't exist yet (called once)."""
    global _bucket_ensured
    if _bucket_ensured:
        return
    client = _get_client()
    try:
        client.head_bucket(Bucket=S3_BUCKET_NAME)
        logger.info(f"[S3] Bucket '{S3_BUCKET_NAME}' exists.")
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in ("404", "NoSuchBucket"):
            logger.info(f"[S3] Creating bucket '{S3_BUCKET_NAME}' in {AWS_REGION}…")
            try:
                if AWS_REGION == "us-east-1":
                    client.create_bucket(Bucket=S3_BUCKET_NAME)
                else:
                    client.create_bucket(
                        Bucket=S3_BUCKET_NAME,
                        CreateBucketConfiguration={"LocationConstraint": AWS_REGION},
                    )
                # Block all public access for security
                client.put_public_access_block(
                    Bucket=S3_BUCKET_NAME,
                    PublicAccessBlockConfiguration={
                        "BlockPublicAcls": True,
                        "IgnorePublicAcls": True,
                        "BlockPublicPolicy": True,
                        "RestrictPublicBuckets": True,
                    },
                )
                logger.info(f"[S3] Bucket '{S3_BUCKET_NAME}' created successfully.")
            except ClientError as create_err:
                logger.warning(f"[S3] Could not create bucket: {create_err}")
                return
        else:
            logger.warning(f"[S3] head_bucket error: {e}")
            return
    _bucket_ensured = True


# ─── Key helpers ──────────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    """Convert arbitrary text to a safe S3 key segment."""
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    return s[:40] or "general"


def _ts() -> str:
    """Millisecond timestamp string for unique keys."""
    return str(int(time.time() * 1000))


# ─── Core upload helpers ───────────────────────────────────────────────────────

def upload_bytes(key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    """
    Upload raw bytes to S3. Returns the S3 key on success, empty string on failure.
    """
    if not _is_configured():
        logger.debug("[S3] Not configured — skipping upload_bytes")
        return ""
    try:
        _ensure_bucket()
        _get_client().put_object(
            Bucket=S3_BUCKET_NAME,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        logger.info(f"[S3] Uploaded {len(data):,} bytes → s3://{S3_BUCKET_NAME}/{key}")
        return key
    except Exception as e:
        logger.warning(f"[S3] upload_bytes failed for key '{key}': {e}")
        return ""


def upload_json(key: str, payload: Any) -> str:
    """Serialize payload to JSON and upload. Returns S3 key or empty string."""
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    return upload_bytes(key, body, "application/json")


def upload_base64(key: str, b64_data: str, content_type: str) -> str:
    """Decode a base64 string and upload. Returns S3 key or empty string."""
    if not b64_data:
        return ""
    try:
        raw = base64.b64decode(b64_data)
        return upload_bytes(key, raw, content_type)
    except Exception as e:
        logger.warning(f"[S3] upload_base64 decode failed for key '{key}': {e}")
        return ""


# ─── Presigned URL ────────────────────────────────────────────────────────────

def get_presigned_url(key: str, expires_in: int = 3600) -> str:
    """
    Generate a pre-signed GET URL for an S3 object.
    Returns the URL string, or empty string if S3 is not configured / key missing.
    """
    if not _is_configured() or not key:
        return ""
    try:
        url = _get_client().generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET_NAME, "Key": key},
            ExpiresIn=expires_in,
        )
        return url
    except Exception as e:
        logger.warning(f"[S3] get_presigned_url failed for key '{key}': {e}")
        return ""


# ─── List keys ────────────────────────────────────────────────────────────────

def list_keys(prefix: str, max_items: int = 50) -> list[dict]:
    """
    List S3 objects under a given prefix.
    Returns list of dicts: [{key, size, last_modified}]
    """
    if not _is_configured():
        return []
    try:
        _ensure_bucket()
        resp = _get_client().list_objects_v2(
            Bucket=S3_BUCKET_NAME,
            Prefix=prefix,
            MaxKeys=max_items,
        )
        items = []
        for obj in resp.get("Contents", []):
            items.append({
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj["LastModified"].isoformat(),
            })
        return items
    except Exception as e:
        logger.warning(f"[S3] list_keys failed for prefix '{prefix}': {e}")
        return []


def download_json(key: str) -> Any:
    """Download and parse a JSON object from S3. Returns None on failure."""
    if not _is_configured() or not key:
        return None
    try:
        resp = _get_client().get_object(Bucket=S3_BUCKET_NAME, Key=key)
        return json.loads(resp["Body"].read())
    except Exception as e:
        logger.warning(f"[S3] download_json failed for key '{key}': {e}")
        return None


# ─── Domain-specific upload functions ─────────────────────────────────────────

def store_session(user_id: str, session_data: dict) -> str:
    """Store a Q&A session as JSON. Returns S3 key."""
    key = f"sessions/{user_id}/{_ts()}.json"
    return upload_json(key, session_data)


def store_quiz_result(user_id: str, quiz_data: dict) -> str:
    """Store a quiz result as JSON. Returns S3 key."""
    key = f"quiz/{user_id}/{_ts()}.json"
    return upload_json(key, quiz_data)


def store_progress(user_id: str, progress_data: dict) -> str:
    """Update the latest progress snapshot for a user. Returns S3 key."""
    key = f"progress/{user_id}/latest.json"
    return upload_json(key, progress_data)


def store_audio(topic: str, audio_b64: str) -> str:
    """Store Polly MP3 audio. Returns S3 key."""
    key = f"audio/{_slugify(topic)}/{_ts()}.mp3"
    return upload_base64(key, audio_b64, "audio/mpeg")


def store_image(topic: str, image_b64: str) -> str:
    """Store a generated PNG image. Returns S3 key."""
    key = f"images/{_slugify(topic)}/{_ts()}.png"
    return upload_base64(key, image_b64, "image/png")


def store_video(topic: str, video_b64: str) -> str:
    """Store a generated MP4 video. Returns S3 key."""
    key = f"videos/{_slugify(topic)}/{_ts()}.mp4"
    return upload_base64(key, video_b64, "video/mp4")


def store_upload(user_id: str, filename: str, file_bytes: bytes) -> str:
    """Store a user-uploaded file. Returns S3 key."""
    safe_name = re.sub(r"[^\w.\-]", "_", filename)[:80]
    key = f"uploads/{user_id}/{_ts()}_{safe_name}"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    mime_map = {
        "pdf": "application/pdf", "txt": "text/plain", "md": "text/markdown",
        "csv": "text/csv", "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "webp": "image/webp", "gif": "image/gif",
    }
    content_type = mime_map.get(ext, "application/octet-stream")
    return upload_bytes(key, file_bytes, content_type)
