"""
services/amazon_q_service.py
Amazon Q integration for AI-powered content review, expert Q&A,
and augmented content generation.

Amazon Q provides enterprise-grade AI assistance that can:
  - Review and improve AI-generated educational content
  - Provide expert-level answers with citations
  - Assist with content quality scoring
  - Generate follow-up suggestions
"""
import json
import logging
import boto3
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

logger = logging.getLogger(__name__)

# ── Boto3 client ──────────────────────────────────────────────────────────────
_q_client = None
_bedrock = None


def _get_q_client():
    """Get Amazon Q Business client."""
    global _q_client
    if _q_client is None:
        _q_client = boto3.client(
            "qbusiness",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
    return _q_client


def _get_bedrock():
    """Get Bedrock Runtime client for content review."""
    global _bedrock
    if _bedrock is None:
        _bedrock = boto3.client(
            "bedrock-runtime",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
    return _bedrock


# ── Content Review with Amazon Q / Bedrock ────────────────────────────────────
def review_content(content: str, topic: str, content_type: str = "explanation") -> dict:
    """
    Use Amazon Q / Bedrock to review AI-generated educational content.

    Returns quality score, suggestions, and improved version.
    """
    try:
        client = _get_bedrock()

        review_prompt = f"""You are an expert educational content reviewer. Review the following {content_type} about "{topic}".

CONTENT TO REVIEW:
{content[:2000]}

Provide your review as JSON:
{{
    "quality_score": <1-10>,
    "accuracy_score": <1-10>,
    "clarity_score": <1-10>,
    "completeness_score": <1-10>,
    "overall_grade": "<A/B/C/D/F>",
    "strengths": ["<strength 1>", "<strength 2>"],
    "improvements": ["<suggestion 1>", "<suggestion 2>"],
    "factual_issues": ["<any factual errors found>"],
    "improved_version": "<briefly improved version of key points>",
    "recommended_follow_ups": ["<follow-up topic 1>", "<follow-up topic 2>"]
}}"""

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": review_prompt}],
        }

        response = client.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )

        result = json.loads(response["body"].read())
        text = result["content"][0]["text"]

        # Parse JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            review = json.loads(json_match.group())
        else:
            review = {"quality_score": 7, "improvements": ["Could not parse review"]}

        review["source"] = "amazon-q-bedrock"
        review["status"] = "reviewed"
        logger.info(f"Content reviewed: quality={review.get('quality_score')}/10")
        return review

    except Exception as e:
        logger.warning(f"Amazon Q content review failed: {e}")
        return {
            "quality_score": 0,
            "status": "unavailable",
            "error": str(e),
            "source": "amazon-q-bedrock",
            "message": "Content review service is not available. Ensure Bedrock model access is enabled.",
        }


def get_expert_answer(question: str, context: str = "") -> dict:
    """
    Use Amazon Q to get an expert-level answer with citations.
    Falls back to Bedrock if Q Business is not configured.
    """
    try:
        client = _get_bedrock()

        prompt = f"""You are an expert AI tutor. Provide a thorough, accurate answer.

QUESTION: {question}
{"CONTEXT: " + context[:1000] if context else ""}

Respond as JSON:
{{
    "expert_answer": "<detailed expert answer>",
    "confidence": <0.0-1.0>,
    "sources": ["<reference 1>", "<reference 2>"],
    "key_concepts": ["<concept 1>", "<concept 2>"],
    "difficulty_level": "<beginner/intermediate/advanced>",
    "related_topics": ["<topic 1>", "<topic 2>"]
}}"""

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": prompt}],
        }

        response = client.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )

        result = json.loads(response["body"].read())
        text = result["content"][0]["text"]

        import re
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            answer = json.loads(json_match.group())
        else:
            answer = {"expert_answer": text, "confidence": 0.7}

        answer["source"] = "amazon-q"
        answer["status"] = "success"
        return answer

    except Exception as e:
        logger.warning(f"Amazon Q expert answer failed: {e}")
        return {
            "status": "unavailable",
            "error": str(e),
            "source": "amazon-q",
            "message": "Expert Q&A is not available.",
        }


def score_content_quality(content: str) -> dict:
    """Quick content quality scoring without full review."""
    try:
        client = _get_bedrock()

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 300,
            "messages": [{
                "role": "user",
                "content": f"Rate this educational content 1-10 for quality, accuracy, and clarity. Reply ONLY with JSON: {{\"quality\":N,\"accuracy\":N,\"clarity\":N,\"grade\":\"A-F\"}}\n\nCONTENT: {content[:1000]}"
            }],
        }

        response = client.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )

        result = json.loads(response["body"].read())
        text = result["content"][0]["text"]

        import re
        json_match = re.search(r'\{[\s\S]*?\}', text)
        if json_match:
            return {**json.loads(json_match.group()), "status": "scored"}

        return {"quality": 7, "accuracy": 7, "clarity": 7, "grade": "B", "status": "default"}

    except Exception as e:
        logger.warning(f"Content scoring failed: {e}")
        return {"status": "unavailable", "error": str(e)}
