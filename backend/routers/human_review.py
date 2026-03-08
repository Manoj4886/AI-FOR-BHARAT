"""
routers/human_review.py
API endpoints for Amazon A2I human review workflows.
"""
import logging
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/human-review", tags=["Augmented AI / Human Review"])


# ── Request Models ────────────────────────────────────────────────────────────
class StartReviewRequest(BaseModel):
    content: str
    topic: str = "General"
    review_type: str = "content_accuracy"
    confidence_score: float = 0.5


class ReviewDecisionRequest(BaseModel):
    review_id: str
    decision: str  # approve / reject / revise
    reviewer_notes: str = ""
    corrected_content: str = ""


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/start")
def start_review(req: StartReviewRequest):
    """Submit content for human review."""
    from services.a2i_service import start_human_review
    return start_human_review(
        content=req.content,
        topic=req.topic,
        review_type=req.review_type,
        confidence_score=req.confidence_score,
    )


@router.get("/status/{review_id}")
def review_status(review_id: str):
    """Check the status of a human review."""
    from services.a2i_service import get_review_status
    return get_review_status(review_id)


@router.post("/decide")
def submit_decision(req: ReviewDecisionRequest):
    """Submit a review decision (approve / reject / revise)."""
    from services.a2i_service import submit_review_decision
    return submit_review_decision(
        review_id=req.review_id,
        decision=req.decision,
        reviewer_notes=req.reviewer_notes,
        corrected_content=req.corrected_content,
    )


@router.get("/pending")
def get_pending():
    """Get all pending reviews in the queue."""
    from services.a2i_service import get_pending_reviews
    return {"pending_reviews": get_pending_reviews()}


@router.get("/stats")
def review_stats():
    """Get review queue statistics."""
    from services.a2i_service import get_review_stats
    return get_review_stats()
