from pydantic import BaseModel
from typing import List, Optional, Literal

SkillLevel = Literal["beginner", "intermediate", "advanced"]

class AskRequest(BaseModel):
    question: str
    skill_level: SkillLevel = "beginner"
    user_id: str = "anonymous"
    user_name: str = ""             # used for personalised greeting

class AskResponse(BaseModel):
    explanation: str                # full explanation with gesture cues (shown on board)
    spoken_text: str = ""           # clean TTS-ready text (sent to Polly)
    topic: str
    skill_level: SkillLevel
    visual_scene: str = ""          # description for graphics engine / board display
    flow_diagram: str = ""          # ASCII flow diagram (if applicable)
    code_blocks: List[dict] = []    # [{language, title, code}] for programming answers
    image_b64: str = ""             # AI-generated image for visual_scene, base64 PNG
    audio_base64: str = ""          # Polly MP3, base64-encoded
    speech_marks: List[dict] = []   # [{time_ms, type, value, viseme_key}]
    video_b64: str = ""             # base64-encoded MP4 (generated when image requested)
    rekognition_labels: List[str] = []  # top Rekognition labels for uploaded images


class QuizRequest(BaseModel):
    topic: str
    skill_level: SkillLevel = "beginner"
    num_questions: int = 3

class QuizOption(BaseModel):
    label: str
    text: str

class QuizQuestion(BaseModel):
    question: str
    options: List[QuizOption]
    answer: str  # label of correct option e.g. "A"

class QuizResponse(BaseModel):
    questions: List[QuizQuestion]
    topic: str

class ProgressEvent(BaseModel):
    user_id: str
    event_type: Literal["question_asked", "quiz_completed"]
    data: dict

class ProgressResponse(BaseModel):
    user_id: str
    questions_asked: int
    quiz_scores: List[dict]
    skill_level: Optional[str] = "beginner"

# ── Vision (image & video generation) ────────────────────────────────────────

class ImageRequest(BaseModel):
    prompt: str                    # visual_scene description from the LLM
    width: int = 512
    height: int = 512

class ImageResponse(BaseModel):
    image_b64: str                 # base64-encoded PNG
    prompt: str
    source: str = "bedrock"        # "bedrock" | "placeholder" | "error"

class VideoRequest(BaseModel):
    image_b64: str                 # base64 PNG from /generate-image
    topic: str
    spoken_text: str

class VideoResponse(BaseModel):
    video_b64: str                 # base64-encoded MP4
    topic: str
