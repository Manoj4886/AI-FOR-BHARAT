"""
Amazon Rekognition service — analyzes uploaded images.

Features:
  - detect_labels()  : identifies objects, scenes, and concepts
  - detect_text()    : OCR — reads any text visible in the image

Returns a natural-language description string that is fed to the AI
as rich image context, replacing the previous generic placeholder.
"""

import logging
import boto3
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "rekognition",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
    return _client


def analyze_image(image_bytes: bytes, filename: str = "") -> str:
    """
    Analyze an image using Amazon Rekognition.

    Parameters
    ----------
    image_bytes : raw bytes of the image file
    filename    : original filename (used in the description)

    Returns
    -------
    A rich natural-language description of the image content,
    suitable for use as AI context.
    """
    try:
        rek = _get_client()
        image_payload = {"Bytes": image_bytes}

        # ── 1. Detect Labels (objects, scenes, concepts) ──────────────────────
        labels_resp = rek.detect_labels(
            Image=image_payload,
            MaxLabels=20,
            MinConfidence=70.0,
        )
        labels = labels_resp.get("Labels", [])

        # Sort by confidence descending, take top 15
        labels.sort(key=lambda x: x["Confidence"], reverse=True)
        top_labels = labels[:15]

        label_parts = []
        for lbl in top_labels:
            name = lbl["Name"]
            conf = round(lbl["Confidence"])
            # Include parent categories for context
            parents = [p["Name"] for p in lbl.get("Parents", [])]
            if parents:
                label_parts.append(f"{name} ({conf}%, category: {', '.join(parents)})")
            else:
                label_parts.append(f"{name} ({conf}%)")

        # ── 2. Detect Text (OCR) ──────────────────────────────────────────────
        text_resp = rek.detect_text(Image=image_payload)
        text_detections = text_resp.get("TextDetections", [])

        # Only take LINE-level detections with reasonable confidence
        detected_lines = [
            d["DetectedText"]
            for d in text_detections
            if d["Type"] == "LINE" and d["Confidence"] >= 75
        ]

        # ── 3. Build natural-language description ─────────────────────────────
        parts = []

        if filename:
            parts.append(f"Image file: {filename}")

        if label_parts:
            parts.append(
                "The image contains: " + "; ".join(label_parts) + "."
            )
        else:
            parts.append("No recognizable objects were detected in the image.")

        if detected_lines:
            text_preview = " | ".join(detected_lines[:10])
            parts.append(f"Text visible in the image: \"{text_preview}\"")
        else:
            parts.append("No readable text was detected in the image.")

        description = "\n".join(parts)
        logger.info(
            f"Rekognition: {len(top_labels)} labels, {len(detected_lines)} text lines for {filename}"
        )
        return description

    except Exception as e:
        logger.warning(f"Rekognition failed ({e}), using fallback description.")
        # Graceful fallback — AI will still try to help
        return (
            f"[IMAGE_UPLOADED] The student uploaded an image file ({filename}). "
            "Rekognition analysis was unavailable. "
            "Please acknowledge it is an image and describe what a typical such image might show, "
            "or ask the student to describe what they see."
        )
