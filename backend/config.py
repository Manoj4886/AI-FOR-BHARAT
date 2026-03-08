import os
from dotenv import load_dotenv

load_dotenv(override=True)

# ── Legacy (kept for Supabase progress tracking) ───────────────────────────
GROQ_API_KEY      = os.getenv("GROQ_API_KEY", "")
SUPABASE_URL      = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
ALLOWED_ORIGINS   = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:5174,http://localhost:5175,"
    "http://localhost:5176,https://*.vercel.app",
).split(",")

# ── AWS ───────────────────────────────────────────────────────────────────
AWS_ACCESS_KEY_ID     = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION            = os.getenv("AWS_REGION", "us-east-1")

# Amazon Bedrock
BEDROCK_MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "anthropic.claude-3-haiku-20240307-v1:0",
)

# Amazon Polly
POLLY_VOICE_ID = os.getenv("POLLY_VOICE_ID", "Matthew")   # neural voice

# Amazon S3
S3_BUCKET_NAME  = os.getenv("S3_BUCKET_NAME", "")
S3_AVATAR_KEY   = os.getenv("S3_AVATAR_KEY", "avatar/teacher.glb")
S3_PREFIX       = os.getenv("S3_PREFIX", "")   # optional e.g. "prod/" or "dev/"

# Amazon Kinesis Video Streams + DeepLens
KINESIS_VIDEO_STREAM_NAME = os.getenv("KINESIS_VIDEO_STREAM_NAME", "saarathi-deeplens-stream")
KINESIS_DATA_RETENTION    = int(os.getenv("KINESIS_DATA_RETENTION_HOURS", "24"))
DEEPLENS_INFERENCE_MODEL  = os.getenv("DEEPLENS_INFERENCE_MODEL", "deeplens-object-detection")

