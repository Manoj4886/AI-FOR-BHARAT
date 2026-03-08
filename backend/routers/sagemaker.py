"""
routers/sagemaker.py
API endpoints for AWS SageMaker visualization and analytics.
"""
import logging
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sagemaker", tags=["SageMaker / Visualization"])


# ── Request Models ────────────────────────────────────────────────────────────
class TrackEventRequest(BaseModel):
    user_id: str = ""
    event_type: str  # question, quiz_attempt, quiz_score, topic_view
    topic: str = ""
    score: float = 0.0


class InvokeEndpointRequest(BaseModel):
    endpoint_name: str
    payload: dict = {}


# ── Visualization Endpoints ───────────────────────────────────────────────────
@router.get("/dashboard")
def full_dashboard(user_id: str = ""):
    """Get the complete visualization dashboard — all charts in one call."""
    from services.sagemaker_service import get_visualization_dashboard
    return get_visualization_dashboard(user_id)


@router.get("/timeline")
def learning_timeline(user_id: str = "", days: int = 7):
    """Get learning timeline chart data (questions/quizzes per day)."""
    from services.sagemaker_service import get_learning_timeline
    return get_learning_timeline(user_id, days)


@router.get("/heatmap")
def topic_heatmap():
    """Get topic difficulty heatmap data."""
    from services.sagemaker_service import get_topic_heatmap
    return get_topic_heatmap()


@router.get("/radar")
def performance_radar(user_id: str = ""):
    """Get performance radar chart (accuracy, breadth, depth, consistency, engagement)."""
    from services.sagemaker_service import get_performance_radar
    return get_performance_radar(user_id)


@router.get("/distribution")
def topic_distribution():
    """Get topic distribution donut chart data."""
    from services.sagemaker_service import get_topic_distribution
    return get_topic_distribution()


@router.get("/sparkline")
def progress_sparkline(user_id: str = "", metric: str = "score"):
    """Get sparkline trend data (score, questions, or topics)."""
    from services.sagemaker_service import get_progress_sparkline
    return get_progress_sparkline(user_id, metric)


# ── Tracking ──────────────────────────────────────────────────────────────────
@router.post("/track")
def track_event(req: TrackEventRequest):
    """Track a learning event for visualization analytics."""
    from services.sagemaker_service import track_event as do_track
    return do_track(
        user_id=req.user_id,
        event_type=req.event_type,
        topic=req.topic,
        score=req.score,
    )


# ── SageMaker Model Endpoints ────────────────────────────────────────────────
@router.post("/invoke")
def invoke_endpoint(req: InvokeEndpointRequest):
    """Invoke a SageMaker endpoint for model inference."""
    from services.sagemaker_service import invoke_sagemaker_endpoint
    return invoke_sagemaker_endpoint(req.endpoint_name, req.payload)


@router.get("/endpoints")
def list_endpoints():
    """List available SageMaker endpoints."""
    from services.sagemaker_service import list_sagemaker_endpoints
    return list_sagemaker_endpoints()


@router.get("/status")
def sagemaker_status():
    """Check SageMaker integration status."""
    from services.sagemaker_service import _learning_events, _topic_stats
    return {
        "status": "active",
        "provider": "aws-sagemaker",
        "tracked_events": len(_learning_events),
        "tracked_topics": len(_topic_stats),
        "features": [
            "learning_timeline",
            "topic_heatmap",
            "performance_radar",
            "topic_distribution",
            "sparklines",
            "model_inference",
            "visualization_dashboard",
        ],
    }
