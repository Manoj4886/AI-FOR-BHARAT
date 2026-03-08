from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_ANON_KEY
import re

_client: Client = None

# A valid Supabase URL looks like https://xxxx.supabase.co
_SUPABASE_OK = bool(SUPABASE_URL and re.match(r'https://[a-z0-9]+\.supabase\.co', SUPABASE_URL))


def get_client() -> Client | None:
    """Return supabase client, or None if credentials aren't configured."""
    global _client
    if not _SUPABASE_OK:
        return None
    if _client is None:
        try:
            _client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        except Exception as e:
            print(f"[Supabase] Could not create client: {e}")
            return None
    return _client


def log_question(user_id: str, question: str, skill_level: str):
    db = get_client()
    if db is None:
        print("[Supabase] Skipping log_question – Supabase not configured")
        return
    try:
        db.table("questions").insert({
            "user_id": user_id,
            "question": question,
            "skill_level": skill_level,
        }).execute()
    except Exception as e:
        print(f"[Supabase] log_question error: {e}")


def log_quiz_score(user_id: str, topic: str, score: int, total: int):
    db = get_client()
    if db is None:
        print("[Supabase] Skipping log_quiz_score – Supabase not configured")
        return
    try:
        db.table("quiz_scores").insert({
            "user_id": user_id,
            "topic": topic,
            "score": score,
            "total": total,
        }).execute()
    except Exception as e:
        print(f"[Supabase] log_quiz_score error: {e}")


def get_progress(user_id: str) -> dict:
    db = get_client()
    if db is None:
        # Return empty progress when Supabase is not configured
        return {
            "user_id": user_id,
            "questions_asked": 0,
            "quiz_scores": [],
            "skill_level": "beginner",
            "recent_questions": [],
        }
    try:
        questions_res = db.table("questions")\
            .select("id, question, skill_level, created_at")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(50)\
            .execute()

        scores_res = db.table("quiz_scores")\
            .select("topic, score, total, created_at")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(50)\
            .execute()

        questions   = questions_res.data or []
        quiz_scores = scores_res.data or []
        skill_level = questions[0]["skill_level"] if questions else "beginner"

        return {
            "user_id": user_id,
            "questions_asked": len(questions),
            "quiz_scores": quiz_scores,
            "skill_level": skill_level,
            "recent_questions": questions[:10],
        }
    except Exception as e:
        print(f"[Supabase] get_progress error: {e}")
        return {
            "user_id": user_id,
            "questions_asked": 0,
            "quiz_scores": [],
            "skill_level": "beginner",
            "recent_questions": [],
        }
