"""
services/sagemaker_service.py
AWS SageMaker integration for visualization, learning analytics,
and AI-powered data insights.

Provides:
  - Learning progress visualization data
  - Topic difficulty heatmaps
  - Performance trend analysis
  - Content embedding visualization (t-SNE / UMAP)
  - Model inference for predictive analytics
  - Chart data generation for frontend rendering
"""
import json
import logging
import math
import time
import boto3
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

logger = logging.getLogger(__name__)

# ── Boto3 clients ─────────────────────────────────────────────────────────────
_sagemaker = None
_sagemaker_runtime = None

# In-memory analytics store
_learning_events: list[dict] = []
_topic_stats: dict[str, dict] = {}


def _get_sagemaker():
    """Get SageMaker client."""
    global _sagemaker
    if _sagemaker is None:
        _sagemaker = boto3.client(
            "sagemaker",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
    return _sagemaker


def _get_sagemaker_runtime():
    """Get SageMaker Runtime client for model inference."""
    global _sagemaker_runtime
    if _sagemaker_runtime is None:
        _sagemaker_runtime = boto3.client(
            "sagemaker-runtime",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
    return _sagemaker_runtime


# ── Track Learning Events ─────────────────────────────────────────────────────
def track_event(
    user_id: str,
    event_type: str,
    topic: str = "",
    score: float = 0.0,
    metadata: dict | None = None,
) -> dict:
    """
    Track a learning event for visualization.
    Event types: question, quiz_attempt, quiz_score, topic_view, session_start
    """
    event = {
        "user_id": user_id,
        "event_type": event_type,
        "topic": topic,
        "score": score,
        "timestamp": time.time(),
        "metadata": metadata or {},
    }
    _learning_events.append(event)

    # Update topic stats
    if topic:
        if topic not in _topic_stats:
            _topic_stats[topic] = {
                "topic": topic,
                "total_questions": 0,
                "total_quizzes": 0,
                "avg_score": 0,
                "scores": [],
                "timestamps": [],
                "difficulty": 0.5,
            }
        stats = _topic_stats[topic]
        stats["timestamps"].append(time.time())
        if event_type == "question":
            stats["total_questions"] += 1
        elif event_type in ("quiz_attempt", "quiz_score"):
            stats["total_quizzes"] += 1
            if score > 0:
                stats["scores"].append(score)
                stats["avg_score"] = sum(stats["scores"]) / len(stats["scores"])

    return {"status": "tracked", "event_count": len(_learning_events)}


# ── Visualization Data Generators ─────────────────────────────────────────────
def get_learning_timeline(user_id: str = "", days: int = 7) -> dict:
    """
    Generate timeline visualization data — questions asked per day,
    quiz scores over time, topics explored.
    """
    cutoff = time.time() - (days * 86400)
    events = [e for e in _learning_events if e["timestamp"] > cutoff]
    if user_id:
        events = [e for e in events if e["user_id"] == user_id]

    # Group by day
    daily = {}
    for e in events:
        day = time.strftime("%Y-%m-%d", time.localtime(e["timestamp"]))
        if day not in daily:
            daily[day] = {"date": day, "questions": 0, "quizzes": 0, "topics": set(), "avg_score": 0, "scores": []}
        daily[day]["questions"] += 1 if e["event_type"] == "question" else 0
        daily[day]["quizzes"] += 1 if e["event_type"] in ("quiz_attempt", "quiz_score") else 0
        if e["topic"]:
            daily[day]["topics"].add(e["topic"])
        if e["score"] > 0:
            daily[day]["scores"].append(e["score"])

    # Convert sets to lists and compute averages
    timeline = []
    for day_data in sorted(daily.values(), key=lambda d: d["date"]):
        day_data["topics"] = list(day_data["topics"])
        day_data["topic_count"] = len(day_data["topics"])
        day_data["avg_score"] = round(sum(day_data["scores"]) / len(day_data["scores"]) * 100, 1) if day_data["scores"] else 0
        del day_data["scores"]
        timeline.append(day_data)

    return {
        "chart_type": "timeline",
        "data": timeline,
        "total_events": len(events),
        "days": days,
    }


def get_topic_heatmap() -> dict:
    """
    Generate topic difficulty heatmap — shows which topics are
    well-understood vs. need more practice.
    """
    heatmap = []
    for topic, stats in _topic_stats.items():
        mastery = min(1.0, stats["avg_score"]) if stats["scores"] else 0.5
        engagement = min(1.0, (stats["total_questions"] + stats["total_quizzes"]) / 20)

        heatmap.append({
            "topic": topic,
            "mastery": round(mastery, 2),
            "engagement": round(engagement, 2),
            "questions_asked": stats["total_questions"],
            "quizzes_taken": stats["total_quizzes"],
            "avg_score": round(stats["avg_score"] * 100, 1) if stats["scores"] else 0,
            "difficulty": round(1 - mastery, 2) if stats["scores"] else 0.5,
            "color": _mastery_to_color(mastery),
        })

    # Sort by engagement (most active first)
    heatmap.sort(key=lambda x: x["engagement"], reverse=True)

    return {
        "chart_type": "heatmap",
        "data": heatmap,
        "total_topics": len(heatmap),
    }


def _mastery_to_color(mastery: float) -> str:
    """Convert mastery level to a hex color (red=low → green=high)."""
    if mastery >= 0.8:
        return "#22c55e"  # green
    elif mastery >= 0.6:
        return "#84cc16"  # lime
    elif mastery >= 0.4:
        return "#eab308"  # yellow
    elif mastery >= 0.2:
        return "#f97316"  # orange
    else:
        return "#ef4444"  # red


def get_performance_radar(user_id: str = "") -> dict:
    """
    Generate radar chart data showing performance across different
    skill dimensions: accuracy, speed, consistency, breadth, depth.
    """
    events = [e for e in _learning_events if not user_id or e["user_id"] == user_id]
    total = len(events)
    topics = set(e["topic"] for e in events if e["topic"])
    scores = [e["score"] for e in events if e["score"] > 0]

    accuracy = round(sum(scores) / len(scores) * 100, 1) if scores else 50
    breadth = min(100, len(topics) * 15)  # 7+ topics = 100%
    depth = min(100, total * 5)  # 20+ events = 100%
    consistency = _calc_consistency(events)
    engagement = min(100, total * 3)

    return {
        "chart_type": "radar",
        "data": {
            "labels": ["Accuracy", "Breadth", "Depth", "Consistency", "Engagement"],
            "values": [accuracy, breadth, depth, consistency, engagement],
            "max_value": 100,
        },
        "summary": {
            "strongest": max(
                [("Accuracy", accuracy), ("Breadth", breadth), ("Depth", depth),
                 ("Consistency", consistency), ("Engagement", engagement)],
                key=lambda x: x[1],
            )[0],
            "weakest": min(
                [("Accuracy", accuracy), ("Breadth", breadth), ("Depth", depth),
                 ("Consistency", consistency), ("Engagement", engagement)],
                key=lambda x: x[1],
            )[0],
        },
    }


def _calc_consistency(events: list) -> float:
    """Calculate learning consistency based on event spread."""
    if len(events) < 2:
        return 50
    timestamps = sorted(e["timestamp"] for e in events)
    gaps = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
    avg_gap = sum(gaps) / len(gaps) if gaps else 86400
    # Ideal gap is ~1 day (86400s). Score drops for longer gaps.
    consistency = max(0, min(100, 100 - (avg_gap / 86400 - 1) * 20))
    return round(consistency, 1)


def get_topic_distribution() -> dict:
    """
    Generate pie/donut chart data showing distribution of
    questions across topics.
    """
    topic_counts = {}
    for e in _learning_events:
        if e["topic"]:
            topic_counts[e["topic"]] = topic_counts.get(e["topic"], 0) + 1

    total = sum(topic_counts.values()) or 1
    colors = ["#8b5cf6", "#3b82f6", "#22c55e", "#eab308", "#ef4444",
              "#ec4899", "#06b6d4", "#f97316", "#84cc16", "#6366f1"]

    slices = []
    for i, (topic, count) in enumerate(sorted(topic_counts.items(), key=lambda x: -x[1])):
        slices.append({
            "topic": topic,
            "count": count,
            "percentage": round(count / total * 100, 1),
            "color": colors[i % len(colors)],
        })

    return {
        "chart_type": "donut",
        "data": slices,
        "total_questions": total,
    }


def get_progress_sparkline(user_id: str = "", metric: str = "score") -> dict:
    """
    Generate sparkline data for quick trend visualization.
    Metrics: score, questions, topics
    """
    events = [e for e in _learning_events if not user_id or e["user_id"] == user_id]
    events.sort(key=lambda e: e["timestamp"])

    points = []
    if metric == "score":
        scores = [e["score"] for e in events if e["score"] > 0]
        # Moving average of last 5
        for i in range(len(scores)):
            window = scores[max(0, i - 4):i + 1]
            points.append(round(sum(window) / len(window) * 100, 1))
    elif metric == "questions":
        # Cumulative questions
        count = 0
        for e in events:
            if e["event_type"] == "question":
                count += 1
                points.append(count)
    elif metric == "topics":
        # Unique topics over time
        seen = set()
        for e in events:
            if e["topic"]:
                seen.add(e["topic"])
                points.append(len(seen))

    return {
        "chart_type": "sparkline",
        "metric": metric,
        "data": points[-50:],  # Last 50 data points
        "trend": "up" if len(points) >= 2 and points[-1] > points[0] else "flat" if len(points) < 2 else "down",
    }


# ── SageMaker Model Inference ─────────────────────────────────────────────────
def invoke_sagemaker_endpoint(endpoint_name: str, payload: dict) -> dict:
    """
    Invoke a SageMaker endpoint for model inference.
    Can be used for content classification, difficulty prediction, etc.
    """
    try:
        runtime = _get_sagemaker_runtime()
        response = runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType="application/json",
            Body=json.dumps(payload),
        )
        result = json.loads(response["Body"].read())
        return {"status": "success", "predictions": result, "endpoint": endpoint_name}
    except Exception as e:
        logger.warning(f"SageMaker endpoint invoke failed: {e}")
        return {"status": "unavailable", "error": str(e), "endpoint": endpoint_name}


def list_sagemaker_endpoints() -> dict:
    """List available SageMaker endpoints."""
    try:
        client = _get_sagemaker()
        response = client.list_endpoints(
            SortBy="CreationTime",
            SortOrder="Descending",
            MaxResults=10,
        )
        endpoints = [
            {
                "name": ep["EndpointName"],
                "status": ep["EndpointStatus"],
                "created": ep["CreationTime"].isoformat() if hasattr(ep["CreationTime"], "isoformat") else str(ep["CreationTime"]),
            }
            for ep in response.get("Endpoints", [])
        ]
        return {"status": "active", "endpoints": endpoints, "count": len(endpoints)}
    except Exception as e:
        logger.warning(f"SageMaker list endpoints failed: {e}")
        return {"status": "unavailable", "endpoints": [], "error": str(e)}


def get_visualization_dashboard(user_id: str = "") -> dict:
    """
    Get a full visualization dashboard with all chart data.
    Single call to populate the entire analytics page.
    """
    return {
        "timeline": get_learning_timeline(user_id),
        "heatmap": get_topic_heatmap(),
        "radar": get_performance_radar(user_id),
        "distribution": get_topic_distribution(),
        "sparklines": {
            "score": get_progress_sparkline(user_id, "score"),
            "questions": get_progress_sparkline(user_id, "questions"),
            "topics": get_progress_sparkline(user_id, "topics"),
        },
        "summary": {
            "total_events": len(_learning_events),
            "total_topics": len(_topic_stats),
            "user_id": user_id or "all",
        },
    }
