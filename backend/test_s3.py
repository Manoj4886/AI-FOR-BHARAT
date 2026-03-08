"""End-to-end S3 test: ask → check storage stats & sessions."""
import httpx
import json

print("=== 1. Asking question ===")
r = httpx.post(
    "http://localhost:8000/ask",
    json={
        "question": "what is photosynthesis",
        "skill_level": "beginner",
        "user_id": "testuser",
        "user_name": "Test",
    },
    timeout=35,
)
print(f"  /ask STATUS: {r.status_code}")

print("\n=== 2. S3 Storage Stats ===")
s = httpx.get("http://localhost:8000/storage/stats", timeout=15).json()
cats = s.get("categories", {})
for k, v in cats.items():
    print(f"  {k}: {v['count']} objects ({v['total_bytes']} bytes)")

print("\n=== 3. Sessions for testuser ===")
se = httpx.get("http://localhost:8000/storage/sessions/testuser", timeout=10).json()
print(f"  Count: {se.get('count', 0)}")
for i in se.get("sessions", []):
    print(f"  {i['key']} ({i['size']} bytes)")

print("\n=== 4. Health ===")
h = httpx.get("http://localhost:8000/health", timeout=5).json()
print(f"  Bucket: {h.get('s3_bucket')}")
print(f"  Configured: {h.get('s3_configured')}")

print("\nDONE")
