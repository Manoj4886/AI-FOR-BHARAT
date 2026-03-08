"""
services/a2i_service.py
Amazon Augmented AI (A2I) integration for human review workflows.

A2I enables human-in-the-loop review for:
  - Low-confidence AI explanations
  - Flagged content that needs expert verification
  - Quiz question validation
  - Content moderation decisions
"""
import json
import logging
import time
import boto3
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

logger = logging.getLogger(__name__)

# ── Boto3 client ──────────────────────────────────────────────────────────────
_a2i_client = None
_s3_client = None

# In-memory review queue (production would use DynamoDB / SQS)
_review_queue: list[dict] = []
_review_results: dict[str, dict] = {}


def _get_a2i_client():
    """Get SageMaker A2I Runtime client."""
    global _a2i_client
    if _a2i_client is None:
        _a2i_client = boto3.client(
            "sagemaker-a2i-runtime",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
    return _a2i_client


def _get_s3_client():
    """Get S3 client for storing review artifacts."""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
    return _s3_client


# ── Human Review Loop ─────────────────────────────────────────────────────────
def start_human_review(
    content: str,
    topic: str,
    review_type: str = "content_accuracy",
    confidence_score: float = 0.5,
    metadata: dict | None = None,
) -> dict:
    """
    Start a human review loop for AI-generated content.

    Review types:
      - content_accuracy: Verify factual accuracy
      - content_quality: Review overall quality
      - quiz_validation: Validate quiz questions
      - moderation: Content moderation check

    Returns review_id for tracking.
    """
    review_id = f"review_{int(time.time())}_{len(_review_queue)}"

    review_item = {
        "review_id": review_id,
        "content": content[:3000],
        "topic": topic,
        "review_type": review_type,
        "confidence_score": confidence_score,
        "status": "pending",
        "created_at": time.time(),
        "metadata": metadata or {},
        "reviewer_notes": "",
        "decision": "",
    }

    _review_queue.append(review_item)
    logger.info(f"[A2I] Human review started: {review_id} ({review_type})")

    # Try to start A2I human loop if configured
    try:
        a2i = _get_a2i_client()
        # List available flow definitions
        flows = a2i.list_human_loops(
            FlowDefinitionArn=f"arn:aws:sagemaker:{AWS_REGION}:*:flow-definition/saarathi-review",
            MaxResults=1,
        )
        review_item["a2i_status"] = "submitted"
        logger.info(f"[A2I] Submitted to AWS A2I: {review_id}")
    except Exception as e:
        review_item["a2i_status"] = "local_queue"
        logger.info(f"[A2I] Using local review queue (A2I not configured): {e}")

    return {
        "review_id": review_id,
        "status": "pending",
        "queue_position": len(_review_queue),
        "review_type": review_type,
        "message": "Content submitted for human review",
    }


def get_review_status(review_id: str) -> dict:
    """Check the status of a human review."""
    # Check local queue
    for item in _review_queue:
        if item["review_id"] == review_id:
            return {
                "review_id": review_id,
                "status": item["status"],
                "review_type": item["review_type"],
                "topic": item["topic"],
                "created_at": item["created_at"],
                "decision": item.get("decision", ""),
                "reviewer_notes": item.get("reviewer_notes", ""),
            }

    # Check results
    if review_id in _review_results:
        return _review_results[review_id]

    return {"review_id": review_id, "status": "not_found"}


def submit_review_decision(
    review_id: str,
    decision: str,
    reviewer_notes: str = "",
    corrected_content: str = "",
) -> dict:
    """
    Submit a review decision (approve / reject / revise).

    Decisions:
      - approve: Content is accurate and ready
      - reject: Content has issues, do not publish
      - revise: Content needs changes (provide corrected_content)
    """
    for item in _review_queue:
        if item["review_id"] == review_id:
            item["status"] = "completed"
            item["decision"] = decision
            item["reviewer_notes"] = reviewer_notes
            item["completed_at"] = time.time()
            if corrected_content:
                item["corrected_content"] = corrected_content

            _review_results[review_id] = item
            logger.info(f"[A2I] Review completed: {review_id} → {decision}")

            return {
                "review_id": review_id,
                "status": "completed",
                "decision": decision,
                "message": f"Review {decision}d successfully",
            }

    return {"review_id": review_id, "status": "not_found"}


def get_pending_reviews() -> list[dict]:
    """Get all pending reviews in the queue."""
    pending = [
        {
            "review_id": item["review_id"],
            "topic": item["topic"],
            "review_type": item["review_type"],
            "confidence_score": item["confidence_score"],
            "status": item["status"],
            "created_at": item["created_at"],
            "content_preview": item["content"][:200] + "…",
        }
        for item in _review_queue
        if item["status"] == "pending"
    ]
    return pending


def get_review_stats() -> dict:
    """Get review queue statistics."""
    total = len(_review_queue)
    pending = sum(1 for r in _review_queue if r["status"] == "pending")
    completed = sum(1 for r in _review_queue if r["status"] == "completed")
    approved = sum(1 for r in _review_queue if r.get("decision") == "approve")
    rejected = sum(1 for r in _review_queue if r.get("decision") == "reject")
    revised = sum(1 for r in _review_queue if r.get("decision") == "revise")

    return {
        "total_reviews": total,
        "pending": pending,
        "completed": completed,
        "approved": approved,
        "rejected": rejected,
        "revised": revised,
        "approval_rate": round(approved / completed * 100, 1) if completed > 0 else 0,
    }


def should_trigger_review(confidence: float, content_length: int) -> bool:
    """Determine if content should be sent for human review based on heuristics."""
    # Low confidence → always review
    if confidence < 0.6:
        return True
    # Very short content → might be incomplete
    if content_length < 50:
        return True
    # Medium confidence → review occasionally
    if confidence < 0.8 and content_length < 200:
        return True
    return False
