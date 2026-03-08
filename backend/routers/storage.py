"""
routers/storage.py
──────────────────
S3 storage API endpoints.

GET  /storage/sessions/{user_id}         – list past Q&A sessions
GET  /storage/quiz/{user_id}             – list quiz results
GET  /storage/progress/{user_id}         – get latest progress snapshot
GET  /storage/audio/{key:path}           – presigned URL for a Polly audio file
GET  /storage/images/{key:path}          – presigned URL for a generated image
GET  /storage/videos/{key:path}          – presigned URL for a generated video
GET  /storage/uploads/{user_id}          – list uploaded files for a user
GET  /storage/stats                      – overall bucket stats
"""
import logging
from fastapi import APIRouter, HTTPException, Query
from services import s3_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/storage", tags=["Storage"])


# ── Session history ────────────────────────────────────────────────────────────

@router.get("/sessions/{user_id}")
async def list_sessions(user_id: str, limit: int = Query(20, le=50)):
    """List recent Q&A sessions stored in S3 for a given user."""
    try:
        items = s3_service.list_keys(f"sessions/{user_id}/", max_items=limit)
        # Enrich with presigned URLs so caller can fetch each session JSON
        for item in items:
            item["url"] = s3_service.get_presigned_url(item["key"])
        return {"user_id": user_id, "sessions": items, "count": len(items)}
    except Exception as e:
        logger.error(f"/storage/sessions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{user_id}/latest")
async def get_latest_session(user_id: str):
    """Fetch the most recent session JSON for a user."""
    try:
        items = s3_service.list_keys(f"sessions/{user_id}/", max_items=50)
        if not items:
            return {"user_id": user_id, "session": None}
        latest_key = sorted(items, key=lambda x: x["key"], reverse=True)[0]["key"]
        data = s3_service.download_json(latest_key)
        return {"user_id": user_id, "session": data, "key": latest_key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Quiz results ───────────────────────────────────────────────────────────────

@router.get("/quiz/{user_id}")
async def list_quiz_results(user_id: str, limit: int = Query(20, le=50)):
    """List quiz results stored in S3 for a user."""
    try:
        items = s3_service.list_keys(f"quiz/{user_id}/", max_items=limit)
        for item in items:
            item["url"] = s3_service.get_presigned_url(item["key"])
        return {"user_id": user_id, "quiz_results": items, "count": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Progress snapshot ─────────────────────────────────────────────────────────

@router.get("/progress/{user_id}")
async def get_s3_progress(user_id: str):
    """Fetch the latest progress snapshot from S3."""
    try:
        data = s3_service.download_json(f"progress/{user_id}/latest.json")
        if data is None:
            return {"user_id": user_id, "progress": None, "source": "s3_empty"}
        return {"user_id": user_id, "progress": data, "source": "s3"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Presigned URLs for media ───────────────────────────────────────────────────

@router.get("/audio/{key:path}")
async def get_audio_url(key: str, expires: int = Query(3600, le=86400)):
    """Get a presigned URL for a stored Polly audio file."""
    url = s3_service.get_presigned_url(key, expires_in=expires)
    if not url:
        raise HTTPException(status_code=404, detail="Audio not found or S3 not configured")
    return {"url": url, "key": key, "expires_in": expires}


@router.get("/images/{key:path}")
async def get_image_url(key: str, expires: int = Query(3600, le=86400)):
    """Get a presigned URL for a stored image."""
    url = s3_service.get_presigned_url(key, expires_in=expires)
    if not url:
        raise HTTPException(status_code=404, detail="Image not found or S3 not configured")
    return {"url": url, "key": key, "expires_in": expires}


@router.get("/videos/{key:path}")
async def get_video_url(key: str, expires: int = Query(3600, le=86400)):
    """Get a presigned URL for a stored video."""
    url = s3_service.get_presigned_url(key, expires_in=expires)
    if not url:
        raise HTTPException(status_code=404, detail="Video not found or S3 not configured")
    return {"url": url, "key": key, "expires_in": expires}


# ── Uploaded files ─────────────────────────────────────────────────────────────

@router.get("/uploads/{user_id}")
async def list_uploads(user_id: str, limit: int = Query(20, le=50)):
    """List files uploaded by a user."""
    try:
        items = s3_service.list_keys(f"uploads/{user_id}/", max_items=limit)
        for item in items:
            item["url"] = s3_service.get_presigned_url(item["key"])
            # Extract original filename from key
            parts = item["key"].rsplit("/", 1)
            item["filename"] = parts[-1].split("_", 1)[-1] if "_" in parts[-1] else parts[-1]
        return {"user_id": user_id, "uploads": items, "count": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Global stats ───────────────────────────────────────────────────────────────

@router.get("/stats")
async def storage_stats():
    """Return counts of stored objects per category."""
    try:
        categories = ["sessions", "quiz", "progress", "audio", "images", "videos", "uploads"]
        stats = {}
        for cat in categories:
            items = s3_service.list_keys(f"{cat}/", max_items=1000)
            total_size = sum(i["size"] for i in items)
            stats[cat] = {"count": len(items), "total_bytes": total_size}
        return {
            "bucket": s3_service.S3_BUCKET_NAME,
            "configured": s3_service._is_configured(),
            "categories": stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
