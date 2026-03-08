"""
Amazon Polly service — neural TTS audio + speech-mark viseme timings.

Returns:
  audio_base64 : base64-encoded MP3 audio string
  speech_marks  : list of { time_ms, type, value } dicts
                  where type=='viseme' gives exact mouth-shape cues
                  and   type=='word'   gives word start times
"""

import base64
import json
import boto3
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, POLLY_VOICE_ID

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "polly",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
    return _client


# ---------------------------------------------------------------------------
# Polly viseme → our viseme key mapping
# Polly uses: p, t, S, T, f, k, i, r, s, u, @, a, e(schwa), E, o, O, sil
# We map to our AvatarModel viseme names
# ---------------------------------------------------------------------------
POLLY_TO_VISEME = {
    "p":   "viseme_PP",
    "t":   "viseme_DD",
    "S":   "viseme_SS",
    "T":   "viseme_TH",
    "f":   "viseme_FF",
    "k":   "viseme_kk",
    "i":   "viseme_I",
    "r":   "viseme_RR",
    "s":   "viseme_SS",
    "u":   "viseme_U",
    "@":   "viseme_aa",
    "a":   "viseme_aa",
    "e":   "viseme_E",
    "E":   "viseme_E",
    "o":   "viseme_O",
    "O":   "viseme_O",
    "sil": "viseme_sil",
}


def synthesize(text: str) -> dict:
    """
    Synthesize speech for `text`.

    Returns
    -------
    dict with keys:
        audio_base64  : str  — base64 MP3
        speech_marks  : list — [{ time_ms, type, value }, ...]
    """
    polly = _get_client()
    voice  = POLLY_VOICE_ID          # e.g. "Matthew"
    engine = "neural"

    # ── 1. Get MP3 audio ─────────────────────────────────────────────────
    audio_resp = polly.synthesize_speech(
        Text=text,
        VoiceId=voice,
        Engine=engine,
        OutputFormat="mp3",
        TextType="text",
    )
    audio_bytes  = audio_resp["AudioStream"].read()
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    # ── 2. Get speech marks (visemes + words) ────────────────────────────
    marks_resp = polly.synthesize_speech(
        Text=text,
        VoiceId=voice,
        Engine=engine,
        OutputFormat="json",
        SpeechMarkTypes=["viseme", "word"],
        TextType="text",
    )
    raw_marks = marks_resp["AudioStream"].read().decode("utf-8")

    speech_marks = []
    for line in raw_marks.strip().splitlines():
        if not line.strip():
            continue
        try:
            mark = json.loads(line)
            entry = {
                "time_ms": mark.get("time", 0),
                "type":    mark.get("type", ""),
                "value":   mark.get("value", ""),
            }
            # Map Polly viseme codes to our avatar viseme names
            if entry["type"] == "viseme":
                entry["viseme_key"] = POLLY_TO_VISEME.get(entry["value"], "viseme_sil")
            speech_marks.append(entry)
        except json.JSONDecodeError:
            continue

    return {
        "audio_base64": audio_base64,
        "speech_marks": speech_marks,
    }
