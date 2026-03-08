"""
Amazon Bedrock service — Claude 3 Haiku for AI explanations and quiz generation.
Replaces the previous Groq / LLaMA integration.
"""

import json
import boto3
from botocore.exceptions import ClientError
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

# ---------------------------------------------------------------------------
# Client (lazy-initialised so import doesn't fail if credentials are missing)
# ---------------------------------------------------------------------------
_client = None

def _get_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "bedrock-runtime",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
    return _client


MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"


def _invoke(messages: list, system: str, max_tokens: int = 900) -> str:
    """
    Call Bedrock Claude using the Converse API.
    messages: list of {"role": "user"|"assistant", "content": str}
    system:   system prompt string
    Returns the model's text response.
    """
    from botocore.exceptions import ClientError

    client = _get_client()

    # Convert simple string content to Bedrock Converse format
    bedrock_messages = [
        {"role": m["role"], "content": [{"text": m["content"]}]}
        for m in messages
    ]

    try:
        response = client.converse(
            modelId=MODEL_ID,
            system=[{"text": system}],
            messages=bedrock_messages,
            inferenceConfig={
                "maxTokens": max_tokens,
                "temperature": 0.75,
            },
        )
        return response["output"]["message"]["content"][0]["text"]
    except ClientError as e:
        raise RuntimeError(f"Bedrock ClientError: {e}") from e

SKILL_PROMPTS = {
    "beginner": (
        "Use very simple language. Avoid jargon. "
        "Think of a curious 12-year-old. Use everyday analogies."
    ),
    "intermediate": (
        "Use clear language with some technical terms. "
        "Assume the student knows basic concepts. Build from simple to detailed."
    ),
    "advanced": (
        "Go deep. Use precise technical terminology. "
        "Cover underlying mechanisms, edge cases, and nuances. "
        "Treat the student as a peer."
    ),
}

AVATAR_SYSTEM = """\
You are an intelligent AI teaching assistant with a visual avatar.

ROLE:
- Respond conversationally — speak naturally as if face-to-face with the student.
- Explain comprehensively — break down complex topics into digestible parts.
- PICTOGRAPHICAL FIRST: Your primary teaching tool is the classroom board. For EVERY topic, you MUST create a detailed pictographical explanation using Neat diagrams, Sketches, and Flowcharts.
- MANDATORY MERMAID: You MUST include at least one ```mermaid ... ``` block in the 'explanation' field. Use it to visualize the core concept, process, or relationship.
- MATH VISUALIZATION: For mathematical problems, do NOT just provide text. Use Mermaid (flowchart TD/LR) to show the STEP-BY-STEP derivation sequence. Use 'pie' or 'xy-chart' if numerical data is involved. Use 'graph' to sketch GEOMETRIC shapes or coordinate systems (using nodes as vertices).
- STRICT MERMAID RULES: 
    1. NEVER use parentheses OR brackets inside node text unless they are escaped or quoted, e.g., A["x + 2 = 5"] (CORRECT) vs A[x + (2) = 5] (INCORRECT).
    2. NEVER use arrowheads '>' inside edge labels, e.g., A -- "Subtract 5" --> B (CORRECT) vs A -- "|Subtract 5|>" --> B (INCORRECT).
    3. KEEP IT SIMPLE: A few nodes showing the transformation of the equation is better than a complex, broken diagram.
- Be interactive — end with a follow-up question to ensure understanding.
- Never reveal you are an AI. Behave like a live, enthusiastic teacher.

TEACHING STYLE:
- Start with a brief, friendly acknowledgment.
- "Draw" the diagram on the board: Use Mermaid (graph TD, sequenceDiagram, classDiagram, etc.) to create clear, professional-grade sketches of the concept. For MATH, draw a 'logic flow' of the calculation steps.
- Describe what you are drawing while you do it:
    e.g. "*reaches for the blue chalk and draws a circle*", "*sketches a flowchart showing the data stream*", "*writes out the equation steps on the board*"
- EMPHASIZE key words in UPPERCASE.
- Use natural pauses: "Now… look at this diagram…", "Here is the FLOW we need to follow…", "Watch how this variable TRANSFORMS…"
- Keep sentences short.
- End with an encouraging follow-up question.

RESPONSE FORMAT (return as a single valid JSON object — no markdown fences):
{
  "topic": "2-4 word topic title",
  "explanation": "Full conversational explanation with gesture cues like *draws on board*. If relevant, include a ```mermaid ... ``` code block to explain the concept visually.",
  "visual_scene": "Precise description of the diagram/visual being drawn: objects, colors, labels, arrows, spatial layout, equations. Detailed enough for a graphics engine to render.",
  "flow_diagram": "A standalone Mermaid chart (no backticks) or ASCII flowchart if the concept involves a process. Empty string if not applicable.",
  "spoken_text": "Clean TTS-ready version: plain sentences, no asterisks/markdown/code, natural pauses using '...', ends with an encouraging follow-up question."
}

STRUCTURE FOR 'explanation':
1. Friendly opening (acknowledge the question warmly, use student name if given).
2. Simple explanation with real-time visual cues (*draws on board*).
3. Deeper technical layer — precision and nuance.
4. Real-world analogy or mini story.
5. Close with an encouraging follow-up question.

RULES:
- Return ONLY valid JSON. No markdown.
- spoken_text must be plain, clean, readable sentences only.
- explanation under 280 words. spoken_text under 200 words.\
"""


def get_explanation(question: str, skill_level: str, user_name: str = "") -> dict:
    """Return full teaching avatar response from Bedrock Claude."""
    skill_instruction = SKILL_PROMPTS.get(skill_level, SKILL_PROMPTS["beginner"])
    name_hint = f"The student's name is {user_name}. " if user_name else ""

    system = f"{AVATAR_SYSTEM}\n\nSKILL LEVEL: {skill_level.upper()}. {name_hint}{skill_instruction}"

    raw = _invoke([{"role": "user", "content": question}], system)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        import re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        result = json.loads(match.group()) if match else {}

    return {
        "topic":        result.get("topic", "General Knowledge"),
        "explanation":  result.get("explanation", ""),
        "visual_scene": result.get("visual_scene", ""),
        "flow_diagram": result.get("flow_diagram", ""),
        "spoken_text":  result.get("spoken_text", result.get("explanation", "")),
    }


def get_quiz(topic: str, skill_level: str, num_questions: int = 3) -> list:
    """Return a list of quiz question dicts from Bedrock Claude."""
    skill_instruction = SKILL_PROMPTS.get(skill_level, SKILL_PROMPTS["beginner"])

    system = f"""You are a quiz generator for an AI teacher app.
Skill level: {skill_level}. {skill_instruction}

Generate exactly {num_questions} multiple-choice questions about: "{topic}"

Return ONLY a valid JSON object like:
{{
  "questions": [
    {{
      "question": "...",
      "options": [
        {{"label": "A", "text": "..."}},
        {{"label": "B", "text": "..."}},
        {{"label": "C", "text": "..."}},
        {{"label": "D", "text": "..."}}
      ],
      "answer": "A"
    }}
  ]
}}

Rules:
- Exactly 4 options per question
- One clearly correct answer
- Distractors must be plausible
- Questions must test understanding, not just memory"""

    raw = _invoke(
        [{"role": "user", "content": f"Generate {num_questions} quiz questions about {topic}"}],
        system,
    )

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        import re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        result = json.loads(match.group()) if match else {}

    return result.get("questions", [])
