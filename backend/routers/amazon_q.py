"""
routers/amazon_q.py
API endpoints for Amazon Q content review and AI assistance.
"""
import logging
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai-assist", tags=["Amazon Q / AI Assist"])


# ── Request Models ────────────────────────────────────────────────────────────
class ReviewRequest(BaseModel):
    content: str
    topic: str = "General"
    content_type: str = "explanation"


class ExpertQueryRequest(BaseModel):
    question: str
    context: str = ""


class ScoreRequest(BaseModel):
    content: str


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/review")
def review_content(req: ReviewRequest):
    """Review AI-generated content for quality, accuracy, and clarity."""
    from services.amazon_q_service import review_content as do_review
    return do_review(req.content, req.topic, req.content_type)


@router.post("/expert-answer")
def get_expert_answer(req: ExpertQueryRequest):
    """Get an expert-level answer with citations using Amazon Q."""
    from services.amazon_q_service import get_expert_answer as do_answer
    return do_answer(req.question, req.context)


@router.post("/score")
def score_content(req: ScoreRequest):
    """Quick quality score for content (quality, accuracy, clarity, grade)."""
    from services.amazon_q_service import score_content_quality
    return score_content_quality(req.content)


@router.get("/status")
def ai_assist_status():
    """Check Amazon Q / AI Assist service availability."""
    try:
        import boto3
        from config import AWS_REGION, AWS_ACCESS_KEY_ID
        client = boto3.client(
            "bedrock-runtime",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
        )
        return {
            "status": "available",
            "provider": "amazon-q-bedrock",
            "region": AWS_REGION,
            "features": ["content_review", "expert_qa", "quality_scoring"],
        }
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}
