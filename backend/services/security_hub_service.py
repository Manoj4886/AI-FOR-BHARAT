"""
services/security_hub_service.py
AWS Security Hub integration for monitoring application security,
compliance checks, and threat detection.

Provides:
  - Security findings aggregation
  - Compliance status checks
  - Custom security event logging
  - Threat detection alerts
"""
import json
import logging
import time
import boto3
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

logger = logging.getLogger(__name__)

# ── Boto3 clients ─────────────────────────────────────────────────────────────
_securityhub = None
_guardduty = None

# In-memory security events (for local tracking)
_security_events: list[dict] = []


def _get_securityhub():
    """Get Security Hub client."""
    global _securityhub
    if _securityhub is None:
        _securityhub = boto3.client(
            "securityhub",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
    return _securityhub


def _get_guardduty():
    """Get GuardDuty client for threat detection."""
    global _guardduty
    if _guardduty is None:
        _guardduty = boto3.client(
            "guardduty",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
    return _guardduty


# ── Security Findings ─────────────────────────────────────────────────────────
def get_security_findings(max_results: int = 20) -> dict:
    """
    Get security findings from AWS Security Hub.
    Returns active findings sorted by severity.
    """
    try:
        client = _get_securityhub()
        response = client.get_findings(
            Filters={
                "WorkflowStatus": [{"Value": "NEW", "Comparison": "EQUALS"}],
                "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
            },
            SortCriteria=[{"Field": "SeverityNormalized", "SortOrder": "desc"}],
            MaxResults=max_results,
        )

        findings = []
        for f in response.get("Findings", []):
            findings.append({
                "id": f.get("Id", "")[-12:],
                "title": f.get("Title", "Unknown"),
                "severity": f.get("Severity", {}).get("Label", "INFORMATIONAL"),
                "severity_score": f.get("Severity", {}).get("Normalized", 0),
                "description": f.get("Description", "")[:200],
                "resource_type": f.get("Resources", [{}])[0].get("Type", "Unknown") if f.get("Resources") else "Unknown",
                "status": f.get("Workflow", {}).get("Status", "NEW"),
                "created": f.get("CreatedAt", ""),
                "source": f.get("ProductName", "Security Hub"),
            })

        return {
            "status": "active",
            "total_findings": len(findings),
            "findings": findings,
            "source": "aws-security-hub",
        }

    except Exception as e:
        logger.warning(f"Security Hub get_findings failed: {e}")
        return {
            "status": "unavailable",
            "total_findings": 0,
            "findings": [],
            "source": "aws-security-hub",
            "message": str(e),
        }


def get_compliance_status() -> dict:
    """
    Get compliance status from Security Hub standards.
    Checks CIS, PCI DSS, and AWS best practices.
    """
    try:
        client = _get_securityhub()
        response = client.get_enabled_standards()

        standards = []
        for s in response.get("StandardsSubscriptions", []):
            standards.append({
                "name": s.get("StandardsArn", "").split("/")[-1],
                "status": s.get("StandardsStatus", "UNKNOWN"),
                "arn": s.get("StandardsSubscriptionArn", ""),
            })

        return {
            "status": "active",
            "standards": standards,
            "total_standards": len(standards),
            "source": "aws-security-hub",
        }

    except Exception as e:
        logger.warning(f"Compliance check failed: {e}")
        return {
            "status": "unavailable",
            "standards": [],
            "message": str(e),
        }


def get_security_score() -> dict:
    """Get the overall security score from Security Hub."""
    try:
        client = _get_securityhub()
        response = client.get_findings(
            Filters={
                "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
            },
            MaxResults=100,
        )

        findings = response.get("Findings", [])
        total = len(findings)

        if total == 0:
            return {"score": 100, "grade": "A+", "status": "excellent", "findings_count": 0}

        # Count by severity
        critical = sum(1 for f in findings if f.get("Severity", {}).get("Label") == "CRITICAL")
        high = sum(1 for f in findings if f.get("Severity", {}).get("Label") == "HIGH")
        medium = sum(1 for f in findings if f.get("Severity", {}).get("Label") == "MEDIUM")
        low = sum(1 for f in findings if f.get("Severity", {}).get("Label") == "LOW")

        # Calculate score (100 - weighted penalties)
        score = max(0, 100 - (critical * 15) - (high * 8) - (medium * 3) - (low * 1))

        grade = (
            "A+" if score >= 95 else
            "A" if score >= 90 else
            "B+" if score >= 85 else
            "B" if score >= 80 else
            "C" if score >= 70 else
            "D" if score >= 60 else "F"
        )

        return {
            "score": score,
            "grade": grade,
            "status": "good" if score >= 80 else "needs_attention" if score >= 60 else "critical",
            "findings_count": total,
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low,
            "source": "aws-security-hub",
        }

    except Exception as e:
        logger.warning(f"Security score calculation failed: {e}")
        return {
            "score": 0,
            "grade": "N/A",
            "status": "unavailable",
            "message": str(e),
        }


# ── Custom Security Event Logging ─────────────────────────────────────────────
def log_security_event(
    event_type: str,
    severity: str = "LOW",
    description: str = "",
    user_id: str = "",
    metadata: dict | None = None,
) -> dict:
    """
    Log a custom security event for tracking.

    Event types:
      - auth_failure: Failed login attempt
      - suspicious_query: Potentially harmful question
      - rate_limit: Rate limit exceeded
      - data_access: Sensitive data access
      - config_change: Configuration change
    """
    event = {
        "event_id": f"evt_{int(time.time())}_{len(_security_events)}",
        "event_type": event_type,
        "severity": severity,
        "description": description,
        "user_id": user_id,
        "timestamp": time.time(),
        "metadata": metadata or {},
    }

    _security_events.append(event)
    logger.info(f"[Security] Event logged: {event_type} ({severity})")

    # Report to Security Hub if configured
    try:
        _report_to_security_hub(event)
    except Exception:
        pass

    return {"event_id": event["event_id"], "status": "logged"}


def _report_to_security_hub(event: dict):
    """Send custom finding to Security Hub."""
    try:
        import os
        account_id = os.getenv("AWS_ACCOUNT_ID", "000000000000")
        client = _get_securityhub()

        severity_map = {
            "CRITICAL": 90, "HIGH": 70, "MEDIUM": 40,
            "LOW": 10, "INFORMATIONAL": 0,
        }

        client.batch_import_findings(Findings=[{
            "SchemaVersion": "2018-10-08",
            "Id": event["event_id"],
            "ProductArn": f"arn:aws:securityhub:{AWS_REGION}:{account_id}:product/{account_id}/default",
            "GeneratorId": "saarathi-security",
            "AwsAccountId": account_id,
            "Types": [f"Software and Configuration Checks/{event['event_type']}"],
            "CreatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(event["timestamp"])),
            "UpdatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "Severity": {"Normalized": severity_map.get(event["severity"], 10)},
            "Title": f"Saarathi: {event['event_type']}",
            "Description": event["description"][:500],
            "Resources": [{
                "Type": "Other",
                "Id": f"saarathi/{event['event_type']}",
                "Region": AWS_REGION,
            }],
        }])
        logger.info(f"[Security] Reported to Security Hub: {event['event_id']}")
    except Exception as e:
        logger.debug(f"Could not report to Security Hub: {e}")


def get_security_events(limit: int = 50) -> list[dict]:
    """Get recent security events."""
    return _security_events[-limit:][::-1]


def get_security_summary() -> dict:
    """Get a summary of security posture."""
    total = len(_security_events)
    last_24h = sum(1 for e in _security_events if time.time() - e["timestamp"] < 86400)
    by_type = {}
    by_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFORMATIONAL": 0}

    for e in _security_events:
        by_type[e["event_type"]] = by_type.get(e["event_type"], 0) + 1
        by_severity[e.get("severity", "LOW")] = by_severity.get(e.get("severity", "LOW"), 0) + 1

    return {
        "total_events": total,
        "last_24h": last_24h,
        "by_type": by_type,
        "by_severity": by_severity,
        "status": "monitoring",
    }
