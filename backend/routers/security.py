"""
routers/security.py
API endpoints for AWS Security Hub integration.
"""
import logging
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/security", tags=["AWS Security Hub"])


# ── Request Models ────────────────────────────────────────────────────────────
class SecurityEventRequest(BaseModel):
    event_type: str  # auth_failure, suspicious_query, rate_limit, etc.
    severity: str = "LOW"  # CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL
    description: str = ""
    user_id: str = ""


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.get("/findings")
def get_findings(max_results: int = 20):
    """Get active security findings from Security Hub."""
    from services.security_hub_service import get_security_findings
    return get_security_findings(max_results)


@router.get("/compliance")
def compliance_status():
    """Get compliance status from enabled Security Hub standards."""
    from services.security_hub_service import get_compliance_status
    return get_compliance_status()


@router.get("/score")
def security_score():
    """Get the overall security score and grade."""
    from services.security_hub_service import get_security_score
    return get_security_score()


@router.post("/event")
def log_event(req: SecurityEventRequest):
    """Log a custom security event."""
    from services.security_hub_service import log_security_event
    return log_security_event(
        event_type=req.event_type,
        severity=req.severity,
        description=req.description,
        user_id=req.user_id,
    )


@router.get("/events")
def get_events(limit: int = 50):
    """Get recent security events."""
    from services.security_hub_service import get_security_events
    return {"events": get_security_events(limit)}


@router.get("/summary")
def security_summary():
    """Get a full security posture summary."""
    from services.security_hub_service import get_security_summary, get_security_score
    score = get_security_score()
    summary = get_security_summary()
    return {**summary, "security_score": score}


@router.get("/status")
def security_status():
    """Check Security Hub service availability."""
    return {
        "status": "active",
        "services": ["security-hub", "guardduty", "custom-events"],
        "features": [
            "findings_aggregation",
            "compliance_checks",
            "security_scoring",
            "custom_event_logging",
            "threat_detection",
        ],
    }
