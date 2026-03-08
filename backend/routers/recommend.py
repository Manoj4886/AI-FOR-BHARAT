"""
routers/recommend.py
Topic recommendations based on user's S3 session history.
"""
import logging
from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# Popular topics organized by category
TOPIC_CATALOG = {
    "Programming Languages": [
        "Python Basics", "JavaScript Fundamentals", "Java OOP",
        "C++ Pointers", "Rust Ownership", "Go Concurrency",
        "TypeScript Types", "Kotlin Coroutines", "Swift Optionals",
        "Ruby Blocks", "PHP Arrays", "SQL Queries", "R Data Frames",
        "Scala Functional Programming", "C# LINQ",
    ],
    "Web Development": [
        "HTML5 Semantic Elements", "CSS Flexbox & Grid", "React Hooks",
        "Node.js Express", "REST API Design", "GraphQL Basics",
        "Next.js SSR", "CSS Animations", "Web Security (XSS/CSRF)",
    ],
    "CS Fundamentals": [
        "Data Structures", "Algorithms", "Big O Notation",
        "Binary Search", "Sorting Algorithms", "Linked Lists",
        "Trees & Graphs", "Dynamic Programming", "Recursion",
        "Stack & Queue", "Hash Tables", "OOP Principles",
    ],
    "AI & Machine Learning": [
        "Machine Learning Basics", "Neural Networks",
        "Deep Learning", "Natural Language Processing",
        "Computer Vision", "Reinforcement Learning",
        "TensorFlow vs PyTorch", "Gradient Descent", "Overfitting",
    ],
    "System Design": [
        "Operating Systems", "DBMS Basics", "Networking (TCP/IP)",
        "Microservices", "Load Balancing", "Caching Strategies",
        "Database Indexing", "CAP Theorem", "Message Queues",
    ],
}


@router.get("/{user_id}")
async def get_recommendations(user_id: str):
    """
    Return topic recommendations based on user's past sessions.
    Pulls session history from S3 and suggests un-explored topics.
    """
    explored = set()

    # Try to get past topics from S3
    try:
        from services.s3_service import list_keys, _client, _is_configured
        import json

        if _is_configured():
            from config import S3_BUCKET_NAME
            keys = list_keys(f"sessions/{user_id}/")
            client = _client()
            for key_info in keys[:20]:  # Check last 20 sessions
                try:
                    obj = client.get_object(Bucket=S3_BUCKET_NAME, Key=key_info)
                    data = json.loads(obj["Body"].read())
                    if "topic" in data:
                        explored.add(data["topic"].lower().strip())
                except Exception:
                    pass
    except Exception as e:
        logger.warning(f"[Recommend] Could not read S3 history: {e}")

    # Build recommendations: prioritize unexplored topics
    recommendations = []
    for category, topics in TOPIC_CATALOG.items():
        cat_rec = []
        for topic in topics:
            is_explored = any(topic.lower() in ex or ex in topic.lower() for ex in explored)
            cat_rec.append({
                "topic": topic,
                "explored": is_explored,
                "question": f"Explain {topic} with examples and code",
            })
        # Sort: unexplored first
        cat_rec.sort(key=lambda x: x["explored"])
        recommendations.append({
            "category": category,
            "topics": cat_rec,
        })

    return {
        "user_id": user_id,
        "explored_count": len(explored),
        "categories": recommendations,
    }


@router.get("/topics/all")
async def get_all_topics():
    """Return the full topic catalog for the topic browser."""
    return TOPIC_CATALOG
