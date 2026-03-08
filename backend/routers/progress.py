from fastapi import APIRouter, HTTPException, Query
from models import ProgressEvent, ProgressResponse
from services.supabase_service import log_quiz_score, get_progress
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/progress")
async def post_progress(req: ProgressEvent):
    try:
        if req.event_type == "quiz_completed":
            log_quiz_score(
                user_id=req.user_id,
                topic=req.data.get("topic", "Unknown"),
                score=req.data.get("score", 0),
                total=req.data.get("total", 0),
            )
            # ── Store quiz result to S3 ───────────────────────────────────
            try:
                from services.s3_service import store_quiz_result
                import time as _time
                store_quiz_result(req.user_id, {
                    "event_type": req.event_type,
                    "topic": req.data.get("topic", "Unknown"),
                    "score": req.data.get("score", 0),
                    "total": req.data.get("total", 0),
                    "timestamp": _time.time(),
                })
            except Exception as s3_err:
                logger.warning(f"[S3] quiz storage failed (non-fatal): {s3_err}")

        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/progress", response_model=ProgressResponse)
async def get_user_progress(user_id: str = Query(..., description="User identifier")):
    try:
        progress = get_progress(user_id)

        # ── Backup progress snapshot to S3 ────────────────────────────────
        try:
            from services.s3_service import store_progress
            store_progress(user_id, progress)
        except Exception as s3_err:
            logger.warning(f"[S3] progress storage failed (non-fatal): {s3_err}")

        return progress
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

