import json
import re
import logging
import httpx
from config import GROQ_API_KEY

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"


def _groq_chat(messages: list, system: str, max_tokens: int = 900) -> str:
    """Direct HTTP call to Groq — avoids ASGI event loop conflicts."""
    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": system}] + messages,
        "temperature": 0.75,
        "max_tokens": max_tokens,
        # NOTE: response_format json_object removed — Groq returns 400 with complex system prompts.
        # The system prompt already instructs "Return ONLY valid JSON" which is sufficient.
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=40) as client:
        resp = client.post(GROQ_API_URL, json=payload, headers=headers)
        resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _parse_json_response(raw: str) -> dict:
    """Robustly extract the JSON object from a Groq response.
    Handles: markdown fences, preamble text, trailing text, control characters,
    trailing commas, truncated JSON, unbalanced brackets.
    NEVER raises — returns a fallback dict on complete failure.
    """

    # Strip markdown code fences (```json ... ```)
    text = re.sub(r"```(?:json)?\s*", "", raw).strip()
    text = text.replace("```", "").strip()

    # Find the first { and last } to isolate the JSON object
    start = text.find("{")
    end   = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    # Strategy 1: Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Remove control characters
    cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Strategy 3: Fix newlines inside strings
    def fix_newlines(m):
        return m.group(0).replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    cleaned2 = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', fix_newlines, cleaned)
    try:
        return json.loads(cleaned2)
    except json.JSONDecodeError:
        pass

    # Strategy 4: Fix trailing commas (,} or ,])
    cleaned3 = re.sub(r',\s*([}\]])', r'\1', cleaned2)
    try:
        return json.loads(cleaned3)
    except json.JSONDecodeError:
        pass

    # Strategy 5: Fix missing commas between key-value pairs (}" or ]")
    cleaned4 = re.sub(r'"\s*\n\s*"', '","', cleaned3)
    try:
        return json.loads(cleaned4)
    except json.JSONDecodeError:
        pass

    # Strategy 6: Truncated JSON — close any open brackets/braces
    truncated = cleaned4
    open_braces = truncated.count('{') - truncated.count('}')
    open_brackets = truncated.count('[') - truncated.count(']')
    # Remove any trailing partial key-value (ends with "," or ":" with no value)
    truncated = re.sub(r',\s*"[^"]*"\s*:\s*$', '', truncated)
    truncated = re.sub(r',\s*$', '', truncated)
    truncated += ']' * max(0, open_brackets)
    truncated += '}' * max(0, open_braces)
    try:
        return json.loads(truncated)
    except json.JSONDecodeError:
        pass

    # Strategy 7: Extract individual fields using regex
    logger.warning(f"[Groq] All JSON parse strategies failed. Extracting fields via regex.")
    fallback = {}
    for field in ['topic', 'explanation', 'visual_scene', 'flow_diagram', 'spoken_text']:
        m = re.search(rf'"{field}"\s*:\s*"((?:[^"\\]|\\.)*)"', cleaned, re.DOTALL)
        if m:
            fallback[field] = m.group(1).replace('\\n', '\n').replace('\\"', '"')
    # Try to extract code_blocks array
    m = re.search(r'"code_blocks"\s*:\s*(\[.*?\])', cleaned, re.DOTALL)
    if m:
        try:
            fallback['code_blocks'] = json.loads(m.group(1))
        except json.JSONDecodeError:
            fallback['code_blocks'] = []
    if fallback:
        return fallback

    # Complete failure — return the raw text as explanation
    logger.error(f"[Groq] Complete JSON parse failure. Returning raw text as explanation.")
    return {
        'topic': 'General Knowledge',
        'explanation': raw[:1500],
        'visual_scene': '',
        'flow_diagram': '',
        'spoken_text': raw[:500],
        'code_blocks': [],
    }



# ── Skill-level depth instructions ──────────────────────────────────────────
SKILL_PROMPTS = {
    "beginner": (
        "Use very simple language. Avoid jargon. "
        "Think of a curious 12-year-old. Use everyday analogies."
    ),
    "intermediate": (
        "Use clear language with some technical terms. "
        "Assume the student knows basic concepts. "
        "Build from simple to detailed."
    ),
    "advanced": (
        "Go deep. Use precise technical terminology. "
        "Cover underlying mechanisms, edge cases, and nuances. "
        "Treat the student as a peer."
    ),
}

# ── Master system prompt ─────────────────────────────────────────────────────
AVATAR_SYSTEM = (
    "You are an intelligent AI teaching assistant with a visual avatar."
    "\n\nROLE:"
    "\n- Respond conversationally — speak naturally as if face-to-face with the student."
    "\n- Explain comprehensively — break down complex topics into digestible parts."
    "\n- PICTOGRAPHICAL FIRST: Your primary teaching tool is the classroom board. "
    "For EVERY topic, you MUST create a detailed pictographical explanation using Neat diagrams, Sketches, and Flowcharts."
    "\n- MANDATORY MERMAID: You MUST include at least one ```mermaid ... ``` block in the 'explanation' field."
    "\n- STRICT MERMAID RULES:"
    "\n  1. ALWAYS quote node labels: A[\"label here\"]"
    "\n  2. NEVER use raw brackets with special chars."
    "\n  3. NEVER use arrowheads inside edge labels. Use: A --> B or A -- \"label\" --> B"
    "\n  4. KEEP IT SIMPLE: max 8 nodes. Short labels only."
    "\n  5. ALWAYS start with a valid type: flowchart TD, sequenceDiagram, graph LR, etc."
    "\n- Be interactive — end with a follow-up question to ensure understanding."
    "\n- Never reveal you are an AI. Behave like a live, enthusiastic teacher."
    "\n\nTEACHING STYLE:"
    "\n- Start with a brief, friendly acknowledgment."
    "\n- Draw the diagram on the board using Mermaid."
    "\n- Describe what you are drawing (e.g. *reaches for chalk and draws a circle*)."
    "\n- EMPHASIZE key words in UPPERCASE."
    "\n- Keep sentences short. End with an encouraging follow-up question."
    "\n\nPROGRAMMING CODE SUPPORT:"
    "\n- When the student asks about ANY programming language (Python, Java, C++, JavaScript, "
    "TypeScript, Rust, Go, C, C#, Ruby, PHP, SQL, HTML, CSS, Kotlin, Swift, R, Scala, etc.):"
    "\n  1. ALWAYS include a 'code_blocks' array in your JSON response."
    "\n  2. Each code block: {\"language\": \"python\", \"title\": \"short title\", \"code\": \"actual runnable code here\"}"
    "\n  3. The code MUST be complete, runnable, properly indented, and well-commented."
    "\n  4. Include 1-3 code blocks showing different aspects (basic example, advanced usage, edge cases)."
    "\n  5. Use the EXACT language name: python, java, cpp, javascript, typescript, rust, go, c, csharp, ruby, php, sql, html, css, kotlin, swift, r, scala."
    "\n  6. In 'explanation', describe WHAT the code does and WHY. The code itself goes ONLY in 'code_blocks'."
    "\n  7. For non-code questions, set code_blocks to an empty array []."
    "\n\nMANDATORY FLOWCHART — flow_diagram field MUST ALWAYS contain a valid Mermaid chart. NEVER leave it empty."
    "\n- For processes/cycles: use flowchart TD with step-by-step nodes and arrows."
    "\n- For hierarchies/categories: use graph TD with parent-child structure."
    "\n- For comparisons: use graph LR with side-by-side branches."
    "\n- For sequences/timelines: use flowchart LR with left-to-right flow."
    "\n- STRICT SYNTAX: Always quote labels with double quotes. Example:"
    "\n  flowchart TD\n    A[\"Start\"] --> B[\"Process\"]\n    B --> C[\"Result\"]\n    C --> D[\"End\"]"
    "\n- Use 4-8 nodes. Keep labels short (2-4 words max). No special characters in labels."
    "\n- The diagram MUST visually represent the core concept being taught."
    "\n\nRESPONSE FORMAT — return ONLY a single valid JSON object with NO markdown fences:"
    "\n{\"topic\": \"2-4 word title\", "
    "\"explanation\": \"Full explanation with mermaid block if relevant.\", "
    "\"code_blocks\": [{\"language\": \"python\", \"title\": \"Example\", \"code\": \"print('hello')\"}], "
    "\"visual_scene\": \"Description of what is drawn on the board.\", "
    "\"flow_diagram\": \"MANDATORY valid Mermaid flowchart. Example: flowchart TD\\n  A[\\\"Input\\\"] --> B[\\\"Process\\\"]\\n  B --> C[\\\"Output\\\"]\", "
    "\"spoken_text\": \"Clean TTS-ready plain sentences. No asterisks or markdown.\"}"
    "\n\nRULES: Return ONLY valid JSON. explanation under 400 words. spoken_text under 220 words."
    "\nflow_diagram MUST ALWAYS have a valid Mermaid chart — NEVER return an empty string for it."
    "\nFor code questions, code_blocks MUST have at least 1 block with real, working code."
)


def get_explanation(question: str, skill_level: str, user_name: str = "", context_messages: list | None = None) -> dict:
    """Ask Groq for a teacher-style explanation. Supports multi-turn conversation context.
    
    Args:
        question: The current question
        skill_level: beginner/intermediate/advanced
        user_name: Optional student name for personalization
        context_messages: Optional list of prior conversation messages for context-aware follow-ups
    """
    try:
        skill_instruction = SKILL_PROMPTS.get(skill_level, SKILL_PROMPTS["beginner"])
        name_hint = f"The student's name is {user_name}. " if user_name else ""

        # Add conversational instruction when we have context
        conv_hint = ""
        if context_messages and len(context_messages) > 1:
            conv_hint = (
                "\n\nCONVERSATION CONTEXT: This is a follow-up question in an ongoing conversation. "
                "Refer to previous answers naturally. If the student says 'tell me more', 'what about...', "
                "'explain further', 'and what is...', etc., relate your answer to the prior context. "
                "Keep your response conversational and connected to what was discussed before."
            )

        system = f"{AVATAR_SYSTEM}\n\nSKILL LEVEL: {skill_level.upper()}. {name_hint}{skill_instruction}{conv_hint}"

        # Use context messages if available, otherwise single question
        if context_messages and len(context_messages) > 1:
            messages = context_messages
        else:
            messages = [{"role": "user", "content": question}]

        raw    = _groq_chat(messages, system, max_tokens=1800)
        result = _parse_json_response(raw)

        return {
            "topic":        result.get("topic", "General Knowledge"),
            "explanation":  result.get("explanation", ""),
            "code_blocks":  result.get("code_blocks", []),
            "visual_scene": result.get("visual_scene", ""),
            "flow_diagram": result.get("flow_diagram", ""),
            "spoken_text":  result.get("spoken_text", result.get("explanation", "")),
        }
    except Exception as e:
        logger.error(f"[Groq] get_explanation failed: {e}")
        return {
            "topic": "General Knowledge",
            "explanation": f"I encountered an issue processing your question about '{question[:50]}'. Please try again — sometimes rephrasing helps!",
            "code_blocks": [],
            "visual_scene": "",
            "flow_diagram": "",
            "spoken_text": f"I had a small issue processing your question. Please try asking again.",
        }


# ── Dedicated system prompt for FILE-based Q&A ──────────────────────────────
FILE_ANALYSIS_SYSTEM = (
    "You are an intelligent AI teaching assistant. The student has uploaded a document or file."
    "\nYour PRIMARY job is to READ the file and answer the student's question using the INFORMATION IN THE FILE."
    "\n\nCRITICAL RULES:"
    "\n1. READ the entire file content between ---FILE START--- and ---FILE END---."
    "\n2. EXTRACT the specific information that answers the student's question."
    "\n3. Base your answer PRIMARILY on the file content."
    "\n4. If information is NOT in the file, say so clearly but still help where you can."
    "\n5. NEVER ignore the file content and answer from general knowledge alone."
    "\n\nTEACHING STYLE:"
    "\n- Explain what you found in the file clearly and concisely."
    "\n- Highlight KEY facts, numbers, names, or steps extracted from the file."
    "\n- Use simple language unless the student asks for technical depth."
    "\n- End with a brief follow-up question to check understanding."
    "\n\nRESPONSE FORMAT — return ONLY a single valid JSON object with NO markdown fences:"
    "\n{\"topic\": \"2-4 word title\", "
    "\"explanation\": \"Detailed answer based on file content. Include mermaid block if helpful.\", "
    "\"visual_scene\": \"What you would draw on a board to summarize the key concept.\", "
    "\"flow_diagram\": \"MANDATORY valid Mermaid flowchart. Example: flowchart TD\\n  A[\\\"Step 1\\\"] --> B[\\\"Step 2\\\"]\\n  B --> C[\\\"Result\\\"]\", "
    "\"spoken_text\": \"Clean TTS-ready summary. No markdown, no asterisks. Plain sentences only.\"}"
    "\n\nRULES: Return ONLY valid JSON. explanation under 400 words. spoken_text under 200 words."
    "\nflow_diagram MUST ALWAYS have a valid Mermaid chart — NEVER return an empty string for it."
    "\nALWAYS reference what you found in the file explicitly."
)


def get_explanation_with_context(question: str, file_text: str, skill_level: str, user_name: str = "") -> dict:
    """Answer a question by deeply analyzing the uploaded file content. Never raises."""
    try:
        skill_instruction = SKILL_PROMPTS.get(skill_level, SKILL_PROMPTS["beginner"])
        name_hint = f"The student's name is {user_name}. " if user_name else ""

        system = f"{FILE_ANALYSIS_SYSTEM}\n\nSKILL LEVEL: {skill_level.upper()}. {name_hint}{skill_instruction}"

        MAX_CHARS = 6000
        file_preview = file_text[:MAX_CHARS].strip()
        if len(file_text) > MAX_CHARS:
            file_preview += f"\n\n[... file continues — showing first {MAX_CHARS} characters ...]"

        messages = [
            {
                "role": "user",
                "content": (
                    f"---FILE START---\n{file_preview}\n---FILE END---\n\n"
                    f"Student's question about this file: {question}"
                ),
            }
        ]

        raw    = _groq_chat(messages, system, max_tokens=1600)
        result = _parse_json_response(raw)

        return {
            "topic":        result.get("topic", "Uploaded File"),
            "explanation":  result.get("explanation", ""),
            "code_blocks":  result.get("code_blocks", []),
            "visual_scene": result.get("visual_scene", ""),
            "flow_diagram": result.get("flow_diagram", ""),
            "spoken_text":  result.get("spoken_text", result.get("explanation", "")),
        }
    except Exception as e:
        logger.error(f"[Groq] get_explanation_with_context failed: {e}")
        return {
            "topic": "Uploaded File",
            "explanation": f"I had trouble analyzing the file for '{question[:50]}'. Please try again.",
            "code_blocks": [],
            "visual_scene": "",
            "flow_diagram": "",
            "spoken_text": "I had trouble analyzing the file. Please try asking again.",
        }



def get_quiz(topic: str, skill_level: str, num_questions: int = 3) -> list:
    skill_instruction = SKILL_PROMPTS.get(skill_level, SKILL_PROMPTS["beginner"])

    system_prompt = f"""You are a quiz generator for an AI teacher app.
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

    try:
        raw    = _groq_chat(
            [{"role": "user", "content": f"Generate {num_questions} quiz questions about {topic}"}],
            system_prompt,
            max_tokens=1200,
        )
        result = _parse_json_response(raw)
        return result.get("questions", [])
    except Exception as e:
        logger.error(f"[Groq] get_quiz failed: {e}")
        return []
