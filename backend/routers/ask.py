from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from models import AskRequest, AskResponse
from services.supabase_service import log_question
import logging
import io
import re

logger = logging.getLogger(__name__)
router = APIRouter()

# Keywords that indicate the user wants a visual/image/video
_IMAGE_PATTERNS = re.compile(
    r"\b(show|draw|visualize|visualise|generate|create|make|produce|render|display|illustrate)"
    r"\s.*(image|picture|photo|diagram|chart|graph|visual|video|map)\b"
    r"|\b(what does .* look like|image of|picture of|video of|diagram of)",
    re.IGNORECASE,
)

def _is_image_request(question: str) -> bool:
    """Return True if the question is asking for an image/video/visual."""
    return bool(_IMAGE_PATTERNS.search(question))


def _get_explanation(question: str, skill_level: str, user_name: str = "", session_id: str = "") -> dict:
    """Use Groq (LLaMA) with optional conversation context for follow-ups."""
    from services.groq_service import get_explanation as groq_explain
    from services.conversation_service import build_conversational_prompt, add_message

    # Build context-aware messages if session exists
    context_messages = None
    if session_id:
        context_messages = build_conversational_prompt(session_id, question)
        # Store the user question in conversation memory
        add_message(session_id, "user", question)

    result = groq_explain(question, skill_level, user_name, context_messages=context_messages)
    logger.info(f"Used Groq for explanation (session={session_id or 'none'}, context_turns={len(context_messages) if context_messages else 0})")

    # Store the assistant response in conversation memory
    if session_id:
        add_message(session_id, "assistant", result.get("explanation", ""), {
            "topic": result.get("topic", ""),
            "has_diagram": bool(result.get("flow_diagram")),
        })

    return result


def _get_explanation_with_context(question: str, file_text: str, skill_level: str, user_name: str = "") -> dict:
    """Use Groq with file context."""
    from services.groq_service import get_explanation_with_context
    result = get_explanation_with_context(question, file_text, skill_level, user_name)
    logger.info("Used Groq with file context")
    return result


def _synthesize(text: str) -> dict:
    """Try Polly first, return empty if Polly fails (frontend uses browser TTS)."""
    try:
        from services.polly_service import synthesize
        result = synthesize(text)
        logger.info(f"Polly: {len(result.get('speech_marks', []))} speech marks")
        return result
    except Exception as e:
        logger.warning(f"Polly failed ({e}), frontend will use browser TTS")
        return {"audio_base64": "", "speech_marks": []}


def _generate_image(topic: str, visual_scene: str, question: str) -> str:
    """Generate an educational image that directly matches the user's question.
    Returns base64 PNG or empty string."""
    try:
        from services.image_service import generate_image

        # Keep it SHORT and DIRECT — the user's question IS the prompt.
        # Don't add walls of generic text that dilute the actual subject.
        prompt = f"{question.strip()}"

        logger.info(f"Image prompt: {prompt}")
        img_result = generate_image(prompt, width=512, height=512)
        logger.info(f"Image generated via: {img_result.get('source', 'unknown')}")
        return img_result.get("image_b64", "")
    except Exception as e:
        logger.warning(f"Image generation failed: {e}")
        return ""


def _generate_video(image_b64: str, topic: str, spoken_text: str, polly_audio_b64: str) -> str:
    """Generate a MP4 slideshow from an already-generated image + Polly narration.
    Returns base64 MP4 or empty string."""
    try:
        if not image_b64:
            return ""
        from services.video_service import generate_video_with_audio
        vid = generate_video_with_audio(image_b64, topic, spoken_text, polly_audio_b64)
        return vid.get("video_b64", "")
    except Exception as e:
        logger.warning(f"Video generation failed: {e}")
        return ""


def _rekognition_analyze(image_bytes: bytes, filename: str) -> tuple:
    """
    Analyze an image with Amazon Rekognition.
    Returns (description_str, top_labels_list).
    """
    try:
        from services.rekognition_service import analyze_image
        description = analyze_image(image_bytes, filename)
        # Extract short label names for the response
        labels = []
        for line in description.split("\n"):
            if "The image contains: " in line:
                raw = line.replace("The image contains: ", "")
                for item in raw.split(";"):
                    name = item.strip().split(" (")[0]
                    if name:
                        labels.append(name)
        return description, labels[:10]
    except Exception as e:
        logger.warning(f"Rekognition unavailable: {e}")
        return (
            f"[IMAGE_UPLOADED] The student uploaded an image file ({filename}). "
            "Describe and analyze the visual content as best you can.",
            [],
        )


def _extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """Extract plain text from an uploaded file based on its extension."""
    fname = (filename or "").lower()

    if fname.endswith(".txt") or fname.endswith(".md") or fname.endswith(".csv"):
        return file_bytes.decode("utf-8", errors="replace")

    if fname.endswith(".pdf"):
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            return "\n".join(
                page.extract_text() or "" for page in reader.pages
            ).strip()
        except Exception as e:
            raise ValueError(f"Could not read PDF: {e}")

    if fname.endswith(".docx"):
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            return "\n".join(p.text for p in doc.paragraphs).strip()
        except Exception as e:
            raise ValueError(f"Could not read DOCX: {e}")

    if any(fname.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".gif"]):
        # Use Amazon Rekognition to get real image description
        description, _ = _rekognition_analyze(file_bytes, filename)
        return description

    raise ValueError(f"Unsupported file type: {filename}. Please upload a .txt, .pdf, .docx, or image file.")


@router.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    try:
        # 1. Get teaching explanation (with conversation context for follow-ups)
        result = _get_explanation(req.question, req.skill_level, req.user_name, session_id=req.user_id)

        # 2. Use spoken_text for Polly (cleaner, no asterisks/markdown)
        tts_text = result.get("spoken_text") or result.get("explanation", "")

        # 3. Synthesise speech (Polly → silent fallback)
        polly = _synthesize(tts_text)

        # 4. Log (best-effort)
        try:
            log_question(req.user_id, req.question, req.skill_level)
        except Exception:
            pass

        # 5. Generate educational image for the visual scene
        image_b64 = ""
        visual_scene = result.get("visual_scene", "")
        topic = result.get("topic", "General Knowledge")
        try:
            image_b64 = _generate_image(topic, visual_scene, req.question)
        except Exception as img_err:
            logger.warning(f"Image generation skipped: {img_err}")

        # 6. Generate interactive video (image + narration) for visual requests
        video_b64 = ""
        if image_b64 and polly["audio_base64"]:
            video_b64 = _generate_video(
                image_b64, topic, tts_text, polly["audio_base64"],
            )

        # 7. ── Store to S3 (fire-and-forget) ─────────────────────────────
        try:
            from services.s3_service import store_session, store_audio, store_video
            import time as _time

            store_session(req.user_id, {
                "question": req.question,
                "topic": topic,
                "explanation": result.get("explanation", ""),
                "spoken_text": tts_text,
                "skill_level": req.skill_level,
                "user_name": req.user_name,
                "timestamp": _time.time(),
                "has_audio": bool(polly["audio_base64"]),
                "has_video": bool(video_b64),
                "has_image": bool(image_b64),
            })
            if polly["audio_base64"]:
                store_audio(topic, polly["audio_base64"])
            if video_b64:
                store_video(topic, video_b64)
        except Exception as s3_err:
            logger.warning(f"[S3] /ask storage failed (non-fatal): {s3_err}")

        return AskResponse(
            explanation=result.get("explanation", ""),
            spoken_text=tts_text,
            topic=topic,
            skill_level=req.skill_level,
            visual_scene=visual_scene,
            flow_diagram=result.get("flow_diagram", ""),
            code_blocks=result.get("code_blocks", []),
            image_b64=image_b64,
            audio_base64=polly["audio_base64"],
            speech_marks=polly["speech_marks"],
            video_b64=video_b64,
        )
    except Exception as e:
        logger.error(f"/ask error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask-with-file", response_model=AskResponse)
async def ask_with_file(
    question: str = Form(...),
    skill_level: str = Form("advanced"),
    user_id: str = Form("anonymous"),
    user_name: str = Form(""),
    file: UploadFile = File(...),
):
    """Answer a question about an uploaded file (txt, pdf, docx, image)."""
    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        # Extract text content from the file
        try:
            file_text = _extract_text_from_file(file_bytes, file.filename or "")
        except ValueError as ve:
            raise HTTPException(status_code=422, detail=str(ve))

        if not file_text.strip():
            raise HTTPException(status_code=422, detail="Could not extract any text from the file.")

        # Get AI explanation using file as context
        result = _get_explanation_with_context(question, file_text, skill_level, user_name)
        tts_text = result.get("spoken_text") or result.get("explanation", "")
        polly = _synthesize(tts_text)

        try:
            log_question(user_id, f"[FILE] {question}", skill_level)
        except Exception:
            pass

        # For image uploads, run Rekognition again to get top labels for response
        rek_labels: list = []
        fname_lower = (file.filename or "").lower()
        if any(fname_lower.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".gif"]):
            _, rek_labels = _rekognition_analyze(file_bytes, file.filename or "")

        # ── Store to S3 (fire-and-forget) ─────────────────────────────────
        try:
            from services.s3_service import store_session, store_upload, store_audio
            import time as _time

            topic = result.get("topic", "Uploaded File")
            store_upload(user_id, file.filename or "unknown", file_bytes)
            store_session(user_id, {
                "question": question,
                "topic": topic,
                "explanation": result.get("explanation", ""),
                "spoken_text": tts_text,
                "skill_level": skill_level,
                "file_upload": file.filename or "",
                "file_size": len(file_bytes),
                "rekognition_labels": rek_labels,
                "timestamp": _time.time(),
            })
            if polly["audio_base64"]:
                store_audio(topic, polly["audio_base64"])
        except Exception as s3_err:
            logger.warning(f"[S3] /ask-with-file storage failed (non-fatal): {s3_err}")

        return AskResponse(
            explanation=result.get("explanation", ""),
            spoken_text=tts_text,
            topic=result.get("topic", "Uploaded File"),
            skill_level=skill_level,
            visual_scene=result.get("visual_scene", ""),
            flow_diagram=result.get("flow_diagram", ""),
            audio_base64=polly["audio_base64"],
            speech_marks=polly["speech_marks"],
            rekognition_labels=rek_labels,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"/ask-with-file error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
