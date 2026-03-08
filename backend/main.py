from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import ask, quiz, progress, vision, storage, recommend, video_stream, auth, amazon_q, human_review, security, sagemaker, conversation, avatar_engines, generative_video, nova_reel, mediaconvert

app = FastAPI(
    title="Smart AI Teacher API",
    description="Backend for the AI Teacher — Groq LLaMA + AWS (Polly, Rekognition, S3)",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+|https://.*\.vercel\.app|https://.*\.loca\.lt",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ask.router,      tags=["Explain"])
app.include_router(quiz.router,     tags=["Quiz"])
app.include_router(progress.router, tags=["Progress"])
app.include_router(vision.router)
app.include_router(storage.router)
app.include_router(recommend.router)
app.include_router(video_stream.router)
app.include_router(auth.router)
app.include_router(amazon_q.router)
app.include_router(human_review.router)
app.include_router(security.router)
app.include_router(sagemaker.router)
app.include_router(conversation.router)
app.include_router(avatar_engines.router)
app.include_router(generative_video.router)
app.include_router(nova_reel.router)
app.include_router(mediaconvert.router)

@app.get("/health")
def health():
    from services.s3_service import _is_configured, S3_BUCKET_NAME
    from config import KINESIS_VIDEO_STREAM_NAME
    return {
        "status": "ok",
        "service": "Saarathi AI Teacher API",
        "s3_configured": _is_configured(),
        "s3_bucket": S3_BUCKET_NAME or "not set",
        "kinesis_stream": KINESIS_VIDEO_STREAM_NAME,
        "aws_services": [
            "bedrock", "polly", "s3", "rekognition",
            "kinesis-video", "amazon-q", "augmented-ai", "security-hub", "sagemaker",
            "conversational-ai", "avatar-engines", "generative-ai-video", "nova-reel",
            "elemental-mediaconvert",
        ],
    }
