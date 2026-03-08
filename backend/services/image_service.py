"""
image_service.py
Generates a 512×512 educational image from a text prompt using AWS Bedrock.

Priority order:
  1. Amazon Nova Canvas        — latest AWS image model (amazon.nova-canvas-v1:0)
  2. Amazon Titan Image Gen v2 — high-quality AWS image model (amazon.titan-image-generator-v2:0)
  3. Amazon Titan Image Gen v1 — stable AWS fallback (amazon.titan-image-generator-v1)
  4. Pollinations.ai           — free external API (no key needed)
  5. Pillow placeholder        — offline gradient + text fallback
"""
import base64
import io
import json
import logging
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)


# ── Boto3 client (shared) ─────────────────────────────────────────────────────
_bedrock = None


def _get_bedrock():
    """Lazily create the Bedrock Runtime client."""
    global _bedrock
    if _bedrock is None:
        import boto3
        from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
        _bedrock = boto3.client(
            "bedrock-runtime",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
    return _bedrock


# ── Prompt enrichment ──────────────────────────────────────────────────────────
def _enrich_prompt(raw_prompt: str) -> str:
    """Add minimal style hints — keep the user's actual question dominant."""
    return f"{raw_prompt}, high quality, detailed illustration"


# ── 1. Amazon Nova Canvas (latest model) ──────────────────────────────────────
def _generate_nova_canvas(prompt: str, width: int = 512, height: int = 512) -> dict:
    """
    Generate an image using Amazon Nova Canvas (amazon.nova-canvas-v1:0).
    
    Nova Canvas supports:
      - Text-to-image generation
      - High quality output up to 4096x4096
      - Better prompt understanding
      - Style control
    """
    enriched = _enrich_prompt(prompt)
    client = _get_bedrock()

    body = {
        "taskType": "TEXT_IMAGE",
        "textToImageParams": {
            "text": enriched,
            "negativeText": (
                "blurry, dark, messy, bad quality, text errors, watermark, "
                "distorted, ugly, low resolution, pixelated, noisy"
            ),
        },
        "imageGenerationConfig": {
            "numberOfImages": 1,
            "quality": "premium",
            "width": width,
            "height": height,
            "cfgScale": 8.0,
            "seed": 0,   # 0 = random for variety
        },
    }

    response = client.invoke_model(
        modelId="amazon.nova-canvas-v1:0",
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )
    result = json.loads(response["body"].read())
    image_b64 = result["images"][0]

    logger.info(f"Nova Canvas image generated ({len(image_b64) // 1024} KB)")
    return {"image_b64": image_b64, "prompt": enriched, "source": "nova-canvas"}


# ── 2. Amazon Titan Image Generator v2 ────────────────────────────────────────
def _generate_titan_v2(prompt: str, width: int = 512, height: int = 512) -> dict:
    """
    Generate an image using Amazon Titan Image Generator v2.
    
    Improvements over v1:
      - Better image quality and coherence
      - Improved text understanding
      - More consistent style output
    """
    enriched = _enrich_prompt(prompt)
    client = _get_bedrock()

    body = {
        "taskType": "TEXT_IMAGE",
        "textToImageParams": {
            "text": enriched,
            "negativeText": (
                "blurry, dark, messy, bad quality, text errors, watermark, "
                "distorted, ugly, low resolution"
            ),
        },
        "imageGenerationConfig": {
            "numberOfImages": 1,
            "quality": "premium",
            "width": width,
            "height": height,
            "cfgScale": 8.0,
            "seed": 0,
        },
    }

    response = client.invoke_model(
        modelId="amazon.titan-image-generator-v2:0",
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )
    result = json.loads(response["body"].read())
    image_b64 = result["images"][0]

    logger.info(f"Titan v2 image generated ({len(image_b64) // 1024} KB)")
    return {"image_b64": image_b64, "prompt": enriched, "source": "titan-v2"}


# ── 3. Amazon Titan Image Generator v1 (stable fallback) ──────────────────────
def _generate_titan_v1(prompt: str, width: int = 512, height: int = 512) -> dict:
    """
    Generate an image using the original Amazon Titan Image Generator v1.
    Most widely available Bedrock image model.
    """
    enriched = _enrich_prompt(prompt)
    client = _get_bedrock()

    body = {
        "taskType": "TEXT_IMAGE",
        "textToImageParams": {
            "text": enriched,
            "negativeText": "blurry, dark, messy, bad quality, text errors, watermark",
        },
        "imageGenerationConfig": {
            "numberOfImages": 1,
            "quality": "standard",
            "width": width,
            "height": height,
            "cfgScale": 8.0,
            "seed": 42,
        },
    }

    response = client.invoke_model(
        modelId="amazon.titan-image-generator-v1",
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )
    result = json.loads(response["body"].read())
    image_b64 = result["images"][0]

    logger.info(f"Titan v1 image generated ({len(image_b64) // 1024} KB)")
    return {"image_b64": image_b64, "prompt": enriched, "source": "titan-v1"}


# ── 4. Pollinations.ai (free external fallback) ───────────────────────────────
def _generate_pollinations(prompt: str, width: int = 512, height: int = 512) -> dict:
    """
    Free Pollinations.ai image API — used when AWS Bedrock models are unavailable.
    """
    enriched = _enrich_prompt(prompt)
    encoded = urllib.parse.quote(enriched)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={width}&height={height}&seed=42&nologo=true&enhance=true"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Saarathi/2.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        img_bytes = resp.read()

    from PIL import Image
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((width, height))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()

    logger.info(f"Pollinations image generated ({len(b64) // 1024} KB)")
    return {"image_b64": b64, "prompt": enriched, "source": "pollinations"}


# ── 5. Pillow placeholder (offline last resort) ───────────────────────────────
def _generate_placeholder(prompt: str, width: int, height: int) -> dict:
    """Generate a gradient placeholder image with text overlay."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import textwrap

        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)
        for y in range(height):
            ratio = y / height
            r = int(80 + ratio * 20)
            g = int(20 + ratio * 160)
            b = int(160 + ratio * 60)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        for cx, cy, radius in [(width // 4, height // 3, 60), (width * 3 // 4, height * 2 // 3, 80)]:
            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                         outline=(255, 255, 255, 80), width=2)

        title = prompt[:60] + ("…" if len(prompt) > 60 else "")
        wrapped = textwrap.fill(title, width=28)
        try:
            font = ImageFont.truetype("arial.ttf", 22)
            small_font = ImageFont.truetype("arial.ttf", 14)
        except IOError:
            font = ImageFont.load_default()
            small_font = font

        txt_x, txt_y = 24, height // 2 - 40
        draw.text((txt_x + 2, txt_y + 2), wrapped, fill=(0, 0, 0, 120), font=font)
        draw.text((txt_x, txt_y), wrapped, fill="white", font=font)
        draw.text((24, height - 30), "Saarathi • Visual Scene", fill=(200, 220, 255), font=small_font)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        return {"image_b64": b64, "prompt": prompt, "source": "placeholder"}
    except Exception as e:
        logger.error(f"Pillow placeholder failed: {e}")
        return {"image_b64": _EMPTY_PNG_B64, "prompt": prompt, "source": "error"}


# ── Main entry point ───────────────────────────────────────────────────────────
def generate_image(prompt: str, width: int = 512, height: int = 512) -> dict:
    """
    Generate an image from *prompt*.
    Tries: Nova Canvas → Titan v2 → Titan v1 → Pollinations → Pillow placeholder.

    Returns:
        {"image_b64": "<base64 PNG>", "prompt": "<enriched prompt>", "source": "<model>"}
    """
    # 1. Amazon Nova Canvas (latest, best quality)
    try:
        return _generate_nova_canvas(prompt, width, height)
    except Exception as e:
        logger.warning(f"Nova Canvas failed ({e}), trying Titan v2…")

    # 2. Amazon Titan Image Generator v2
    try:
        return _generate_titan_v2(prompt, width, height)
    except Exception as e:
        logger.warning(f"Titan v2 failed ({e}), trying Titan v1…")

    # 3. Amazon Titan Image Generator v1
    try:
        return _generate_titan_v1(prompt, width, height)
    except Exception as e:
        logger.warning(f"Titan v1 failed ({e}), trying Pollinations…")

    # 4. Pollinations.ai (free external)
    try:
        return _generate_pollinations(prompt, width, height)
    except Exception as e:
        logger.warning(f"Pollinations failed ({e}), using Pillow placeholder…")

    # 5. Pillow placeholder (offline)
    return _generate_placeholder(prompt, width, height)


# 1×1 white PNG in base64 (absolute last resort)
_EMPTY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI6QAAAABJRU5ErkJggg=="
)
