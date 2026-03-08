"""
video_service.py
Assembles a short MP4 slideshow (~6s) from:
  1. A topic title card (gradient + topic name)
  2. The AI-generated visual scene image
  3. A caption card with the spoken explanation

Uses imageio (ffmpeg plugin) + Pillow. Outputs base64-encoded MP4.
"""
import base64
import io
import logging
import textwrap
import numpy as np

logger = logging.getLogger(__name__)

FPS = 24
TOTAL_SECONDS = 7
WIDTH, HEIGHT = 512, 512


# ── Helpers ────────────────────────────────────────────────────────────────────

def _load_pil():
    from PIL import Image, ImageDraw, ImageFont
    return Image, ImageDraw, ImageFont


def _pil_to_np(pil_img) -> np.ndarray:
    """Convert a PIL RGB image to a numpy uint8 array."""
    return np.array(pil_img.convert("RGB"), dtype=np.uint8)


def _gradient_bg(w: int, h: int, c1=(30, 10, 80), c2=(10, 90, 120)):
    """Return a PIL Image with a linear gradient background."""
    Image, _, _ = _load_pil()
    img = Image.new("RGB", (w, h))
    pixels = img.load()
    for y in range(h):
        ratio = y / h
        r = int(c1[0] + ratio * (c2[0] - c1[0]))
        g = int(c1[1] + ratio * (c2[1] - c1[1]))
        b = int(c1[2] + ratio * (c2[2] - c1[2]))
        for x in range(w):
            pixels[x, y] = (r, g, b)
    return img


def _get_font(size: int):
    Image, ImageDraw, ImageFont = _load_pil()
    for name in ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "FreeSans.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _title_card(topic: str, w: int = WIDTH, h: int = HEIGHT) -> np.ndarray:
    """Render a title card frame (numpy array)."""
    Image, ImageDraw, ImageFont = _load_pil()
    img = _gradient_bg(w, h, (20, 10, 60), (5, 80, 110))
    draw = ImageDraw.Draw(img)

    # Decorative corner glows
    for cx, cy, r in [(0, 0, 120), (w, h, 150)]:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(100, 50, 200, 0))

    # AI Teacher label
    small = _get_font(16)
    draw.text((w // 2 - 52, 60), "🎓  AI Teacher", fill=(160, 210, 255), font=small)

    # Topic title
    title_font = _get_font(30)
    wrapped = textwrap.fill(topic[:80], width=20)
    bbox = draw.textbbox((0, 0), wrapped, font=title_font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx, ty = (w - tw) // 2, (h - th) // 2 - 20

    # Glow shadow
    for offset in [(3, 3), (-3, 3), (3, -3), (-3, -3)]:
        draw.text((tx + offset[0], ty + offset[1]), wrapped, fill=(80, 0, 200), font=title_font)
    draw.text((tx, ty), wrapped, fill=(255, 255, 255), font=title_font)

    # Divider line
    draw.line([(w // 4, h // 2 + 40), (3 * w // 4, h // 2 + 40)], fill=(120, 180, 255), width=2)
    draw.text((w // 2 - 50, h // 2 + 55), "Visual Explanation", fill=(140, 200, 255), font=small)

    return _pil_to_np(img)


def _image_card(image_b64: str, topic: str, w: int = WIDTH, h: int = HEIGHT) -> np.ndarray:
    """Load the AI-generated image and overlay a subtle label."""
    Image, ImageDraw, _ = _load_pil()
    img_data = base64.b64decode(image_b64)
    img = Image.open(io.BytesIO(img_data)).convert("RGB").resize((w, h))
    draw = ImageDraw.Draw(img)

    # Bottom label bar
    bar_h = 36
    for y in range(h - bar_h, h):
        alpha = (y - (h - bar_h)) / bar_h
        for x in range(w):
            r, g, b = img.getpixel((x, y))
            img.putpixel((x, y), (
                int(r * (1 - alpha) + 10 * alpha),
                int(g * (1 - alpha) + 20 * alpha),
                int(b * (1 - alpha) + 50 * alpha),
            ))

    font = _get_font(14)
    label = f"⚡ {topic[:40]}"
    draw.text((12, h - 26), label, fill=(200, 230, 255), font=font)
    draw.text((w - 110, h - 26), "AI Generated", fill=(160, 200, 255), font=font)

    return _pil_to_np(img)


def _caption_card(text: str, topic: str, w: int = WIDTH, h: int = HEIGHT) -> np.ndarray:
    """Render a text caption card."""
    Image, ImageDraw, _ = _load_pil()
    img = _gradient_bg(w, h, (5, 50, 80), (20, 10, 60))
    draw = ImageDraw.Draw(img)

    # Header
    hfont = _get_font(18)
    draw.text((20, 24), f"📖  {topic}", fill=(180, 230, 255), font=hfont)
    draw.line([(20, 56), (w - 20, 56)], fill=(80, 160, 220), width=1)

    # Body text
    body_font = _get_font(16)
    clean = text.replace("*", "").replace("#", "").strip()
    wrapped_lines = textwrap.wrap(clean[:400], width=40)
    y = 72
    for line in wrapped_lines[:14]:
        draw.text((20, y), line, fill=(230, 245, 255), font=body_font)
        y += 22
        if y > h - 50:
            break

    # Footer
    small = _get_font(13)
    draw.text((20, h - 28), "AI Teacher  •  Key Points", fill=(100, 160, 210), font=small)

    return _pil_to_np(img)


def _crossfade_frames(frame_a: np.ndarray, frame_b: np.ndarray, n: int = 12):
    """Yield n crossfade numpy frames from frame_a to frame_b."""
    for i in range(n):
        t = i / n
        yield (frame_a * (1 - t) + frame_b * t).astype(np.uint8)


# ── Main entry point ───────────────────────────────────────────────────────────

def generate_video(image_b64: str, topic: str, spoken_text: str) -> dict:
    """
    Assemble a ~7s educational MP4 slideshow:
      0–2s  : Title card
      2–4s  : AI-generated image
      4–7s  : Caption card with key points
    With 12-frame crossfades between each slide.

    Returns:
        {"video_b64": "<base64 MP4>", "topic": topic}
    """
    try:
        import imageio

        title  = _title_card(topic)
        img_fr = _image_card(image_b64, topic)
        caption = _caption_card(spoken_text, topic)

        hold_short = FPS * 2   # 2s per slide
        hold_long  = FPS * 3   # 3s for caption

        frames = []
        # Title card (2s)
        frames += [title] * hold_short
        # Crossfade to image
        frames += list(_crossfade_frames(title, img_fr))
        # Image card (2s)
        frames += [img_fr] * hold_short
        # Crossfade to caption
        frames += list(_crossfade_frames(img_fr, caption))
        # Caption card (3s)
        frames += [caption] * hold_long

        buf = io.BytesIO()
        writer = imageio.get_writer(buf, format="mp4", fps=FPS, codec="libx264",
                                    output_params=["-pix_fmt", "yuv420p"])
        for f in frames:
            writer.append_data(f)
        writer.close()

        b64 = base64.b64encode(buf.getvalue()).decode()
        logger.info(f"Video generated: {len(frames)} frames, {len(b64)//1024} KB")
        return {"video_b64": b64, "topic": topic}

    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        return {"video_b64": "", "topic": topic, "error": str(e)}


def generate_video_with_audio(
    image_b64: str,
    topic: str,
    spoken_text: str,
    audio_b64: str = "",
) -> dict:
    """
    Generate an MP4 slideshow with embedded Polly MP3 audio narration.

    Strategy:
      1. Generate the silent MP4 slideshow (same as generate_video)
      2. If audio_b64 is provided, use ffmpeg (subprocess) to mux the audio track in
      3. Fall back to the silent video if ffmpeg fails

    Returns:
        {"video_b64": "<base64 MP4>", "topic": topic}
    """
    # Step 1: generate the silent video
    silent = generate_video(image_b64, topic, spoken_text)
    silent_b64 = silent.get("video_b64", "")

    if not silent_b64:
        return {"video_b64": "", "topic": topic}

    if not audio_b64:
        # No audio provided → return silent video as-is
        return silent

    # Step 2: mux audio into video using ffmpeg
    try:
        import subprocess
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = os.path.join(tmpdir, "silent.mp4")
            audio_path = os.path.join(tmpdir, "narration.mp3")
            output_path = os.path.join(tmpdir, "final.mp4")

            # Write the silent MP4
            video_bytes = base64.b64decode(silent_b64)
            with open(video_path, "wb") as f:
                f.write(video_bytes)

            # Write the Polly MP3
            audio_bytes = base64.b64decode(audio_b64)
            with open(audio_path, "wb") as f:
                f.write(audio_bytes)

            # Run ffmpeg to combine: video + audio, truncate to shorter of the two
            result = subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", video_path,
                    "-i", audio_path,
                    "-c:v", "copy",       # copy video stream (no re-encode)
                    "-c:a", "aac",        # encode audio to AAC for MP4 container
                    "-shortest",          # stop at the shorter stream
                    "-movflags", "+faststart",
                    output_path,
                ],
                capture_output=True,
                timeout=60,
            )

            if result.returncode != 0:
                err = result.stderr.decode(errors="replace")[:300]
                logger.warning(f"ffmpeg mux failed: {err}, returning silent video")
                return silent

            with open(output_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()

            logger.info(f"Video+audio generated: {len(b64)//1024} KB for topic '{topic}'")
            return {"video_b64": b64, "topic": topic}

    except FileNotFoundError:
        logger.warning("ffmpeg not found — returning silent video. Install ffmpeg to enable audio.")
        return silent
    except subprocess.TimeoutExpired:
        logger.warning("ffmpeg timed out — returning silent video")
        return silent
    except Exception as e:
        logger.warning(f"Audio mux error: {e} — returning silent video")
        return silent
