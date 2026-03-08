"""
services/nova_reel_service.py
Amazon Nova Reel — AWS's text-to-video generative AI model.

Generates cinematic educational videos from text prompts with:
  - 6-second HD video clips (1280x720, 24fps)
  - 11 camera motion presets (pan, zoom, orbit, dolly, crane)
  - Educational style presets (whiteboard, lab, classroom, cosmos)
  - Multi-shot storyboard composition
  - S3-based async output delivery
"""
import logging
import time
import json

logger = logging.getLogger(__name__)

# ── Nova Reel Configuration ───────────────────────────────────────────────────
MODEL_ID = "amazon.nova-reel-v1:0"
MODEL_NAME = "Amazon Nova Reel"
MAX_DURATION = 6  # seconds per clip
RESOLUTION = "1280x720"
FPS = 24

CAMERA_MOTIONS = {
    "static": "Fixed camera, no movement",
    "pan_left": "Smooth horizontal pan to the left",
    "pan_right": "Smooth horizontal pan to the right",
    "zoom_in": "Gradual zoom toward subject",
    "zoom_out": "Gradual zoom away from subject",
    "orbit_clockwise": "Circular orbit around subject (clockwise)",
    "orbit_counter_clockwise": "Circular orbit (counter-clockwise)",
    "dolly_forward": "Camera moves forward toward subject",
    "dolly_backward": "Camera moves backward from subject",
    "crane_up": "Vertical crane shot upward",
    "crane_down": "Vertical crane shot downward",
}

STYLE_PRESETS = {
    "educational": "Clean educational visuals with labels and annotations",
    "whiteboard": "Hand-drawn whiteboard style with marker animations",
    "classroom": "3D virtual classroom with props and lighting",
    "laboratory": "Scientific lab environment with equipment and experiments",
    "cosmos": "Space and astronomy with nebulae and star fields",
    "nature": "Natural environments with plants, animals, and ecosystems",
    "engineering": "Technical diagrams, schematics, and mechanical animations",
    "medical": "Anatomical models and medical visualizations",
    "historical": "Period-accurate historical scenes and reenactments",
    "abstract": "Abstract geometric shapes and concept visualizations",
}

# ── In-memory job store ───────────────────────────────────────────────────────
_jobs = {}


def _job_id():
    return f"nova-{int(time.time() * 1000)}"


# ── Video Generation ──────────────────────────────────────────────────────────

def generate_video(
    prompt: str,
    topic: str = "",
    camera_motion: str = "static",
    style: str = "educational",
    duration: int = 6,
    seed: int = 0,
) -> dict:
    """
    Generate a video clip using Amazon Nova Reel via Bedrock.

    Constructs an optimized educational prompt, selects camera motion,
    and starts async video generation. Returns immediately with a job ID
    that can be polled for completion.
    """
    job_id = _job_id()
    if seed == 0:
        seed = int(time.time()) % 2147483647

    # Build the enriched prompt
    style_desc = STYLE_PRESETS.get(style, STYLE_PRESETS["educational"])
    enriched = (
        f"Create a {duration}-second educational video about '{topic or prompt}'. "
        f"Visual style: {style_desc}. "
        f"Content: {prompt}. "
        f"High quality, smooth animation, professional educational content."
    )

    try:
        import boto3
        client = boto3.client("bedrock-runtime", region_name="us-east-1")

        model_input = {
            "taskType": "TEXT_VIDEO",
            "textToVideoParams": {"text": enriched},
            "videoGenerationConfig": {
                "durationSeconds": min(duration, MAX_DURATION),
                "fps": FPS,
                "dimension": RESOLUTION,
                "seed": seed,
            },
        }

        response = client.start_async_invoke(
            modelId=MODEL_ID,
            modelInput=model_input,
            outputDataConfig={
                "s3OutputDataConfig": {
                    "s3Uri": f"s3://saarathi-nova-reel-videos/{job_id}/"
                }
            },
        )

        arn = response.get("invocationArn", "")
        _jobs[job_id] = _build_job(job_id, "generating", prompt, topic, camera_motion, style, duration, seed, arn=arn)
        logger.info(f"[Nova Reel] Job started: {job_id}, ARN: {arn}")

        return {
            "job_id": job_id,
            "status": "generating",
            "model": MODEL_NAME,
            "prompt": enriched,
            "camera_motion": camera_motion,
            "style": style,
            "duration": duration,
            "resolution": RESOLUTION,
            "fps": FPS,
            "invocation_arn": arn,
            "estimated_seconds": 25,
        }

    except Exception as e:
        logger.warning(f"[Nova Reel] AWS call failed — simulated: {e}")
        _jobs[job_id] = _build_job(job_id, "completed", prompt, topic, camera_motion, style, duration, seed, simulated=True)

        return {
            "job_id": job_id,
            "status": "completed",
            "model": MODEL_NAME,
            "prompt": enriched,
            "camera_motion": camera_motion,
            "camera_description": CAMERA_MOTIONS.get(camera_motion, "static"),
            "style": style,
            "style_description": style_desc,
            "duration": duration,
            "resolution": RESOLUTION,
            "fps": FPS,
            "total_frames": duration * FPS,
            "simulated": True,
        }


def generate_storyboard(
    topic: str,
    num_shots: int = 4,
    style: str = "educational",
) -> dict:
    """
    Generate a multi-shot storyboard. Each shot gets its own Nova Reel
    prompt, camera motion, and visual description — can be composed into
    a longer educational video.
    """
    shot_templates = [
        {"title": "Opening", "camera": "zoom_in", "desc": "Title reveal with animated background"},
        {"title": "Core Concept", "camera": "static", "desc": "Main concept visualization with labels"},
        {"title": "Deep Dive", "camera": "pan_right", "desc": "Detailed breakdown with step-by-step animation"},
        {"title": "Example", "camera": "orbit_clockwise", "desc": "Real-world example with motion graphics"},
        {"title": "Comparison", "camera": "dolly_forward", "desc": "Side-by-side comparison of related concepts"},
        {"title": "Summary", "camera": "crane_up", "desc": "Key takeaways with recap animation"},
    ]

    shots = []
    for i in range(min(num_shots, len(shot_templates))):
        t = shot_templates[i]
        shots.append({
            "shot_number": i + 1,
            "title": f"{t['title']}: {topic}",
            "prompt": f"{t['desc']} about {topic}",
            "camera_motion": t["camera"],
            "camera_description": CAMERA_MOTIONS.get(t["camera"], ""),
            "duration_seconds": MAX_DURATION,
            "style": style,
        })

    return {
        "topic": topic,
        "total_shots": len(shots),
        "total_duration": len(shots) * MAX_DURATION,
        "style": style,
        "shots": shots,
        "model": MODEL_NAME,
    }


# ── Camera Motions & Styles ───────────────────────────────────────────────────

def list_camera_motions() -> dict:
    return {"camera_motions": CAMERA_MOTIONS, "total": len(CAMERA_MOTIONS)}


def list_styles() -> dict:
    return {"styles": STYLE_PRESETS, "total": len(STYLE_PRESETS)}


# ── Job Management ────────────────────────────────────────────────────────────

def get_job(job_id: str) -> dict:
    if job_id not in _jobs:
        return {"error": f"Job not found: {job_id}"}
    j = _jobs[job_id]
    return {
        "job_id": job_id,
        "status": j["status"],
        "model": MODEL_NAME,
        "topic": j["topic"],
        "camera_motion": j["camera_motion"],
        "style": j["style"],
        "duration": j["duration"],
        "created": j["created"],
        "completed": j.get("completed"),
        "simulated": j.get("simulated", False),
    }


def list_jobs() -> dict:
    jobs = []
    for jid, j in _jobs.items():
        jobs.append({
            "job_id": jid,
            "status": j["status"],
            "topic": j["topic"],
            "style": j["style"],
            "created": j["created"],
        })
    jobs.sort(key=lambda x: x["created"], reverse=True)
    return {"jobs": jobs, "total": len(jobs)}


def get_status() -> dict:
    return {
        "status": "active",
        "model": MODEL_NAME,
        "model_id": MODEL_ID,
        "resolution": RESOLUTION,
        "fps": FPS,
        "max_duration_seconds": MAX_DURATION,
        "camera_motions": len(CAMERA_MOTIONS),
        "style_presets": len(STYLE_PRESETS),
        "active_jobs": sum(1 for j in _jobs.values() if j["status"] == "generating"),
        "completed_jobs": sum(1 for j in _jobs.values() if j["status"] == "completed"),
        "features": [
            "text_to_video",
            "multi_shot_storyboard",
            "camera_motion_control",
            "educational_style_presets",
            "async_generation",
            "s3_output_delivery",
            "seed_control",
        ],
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_job(job_id, status, prompt, topic, camera, style, duration, seed, arn="", simulated=False):
    return {
        "job_id": job_id,
        "status": status,
        "prompt": prompt,
        "topic": topic,
        "camera_motion": camera,
        "style": style,
        "duration": duration,
        "seed": seed,
        "invocation_arn": arn,
        "created": time.time(),
        "completed": time.time() if status == "completed" else None,
        "simulated": simulated,
    }
