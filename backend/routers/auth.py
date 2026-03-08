"""
routers/auth.py
Simple authentication endpoints — register, login, check session.
Uses in-memory store with localStorage tokens (no DB required).
Optionally persists to Supabase if configured.
"""
import hashlib
import logging
import secrets
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])

# ── In-memory user store (persists until server restarts) ─────────────────────
# In production, use Supabase / DynamoDB / any real DB.
_users: dict[str, dict] = {}     # email → {name, email, password_hash, created}
_sessions: dict[str, dict] = {}  # token → {email, name, created}


# ── Helpers ───────────────────────────────────────────────────────────────────
def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _create_token(email: str, name: str) -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = {"email": email, "name": name, "created": time.time()}
    return token


# ── Models ────────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    success: bool
    token: str = ""
    name: str = ""
    email: str = ""
    message: str = ""


class TokenCheckRequest(BaseModel):
    token: str


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest):
    """Create a new user account."""
    email = req.email.strip().lower()
    name = req.name.strip()
    password = req.password

    if not name or len(name) < 2:
        raise HTTPException(status_code=400, detail="Name must be at least 2 characters")
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Please enter a valid email address")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    if email in _users:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    _users[email] = {
        "name": name,
        "email": email,
        "password_hash": _hash_password(password),
        "created": time.time(),
    }

    token = _create_token(email, name)
    logger.info(f"[Auth] New user registered: {email}")

    return AuthResponse(
        success=True,
        token=token,
        name=name,
        email=email,
        message="Account created successfully!",
    )


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest):
    """Sign in with email and password."""
    email = req.email.strip().lower()
    password = req.password

    user = _users.get(email)
    if not user:
        raise HTTPException(status_code=401, detail="No account found with this email")

    if user["password_hash"] != _hash_password(password):
        raise HTTPException(status_code=401, detail="Incorrect password")

    token = _create_token(email, user["name"])
    logger.info(f"[Auth] User logged in: {email}")

    return AuthResponse(
        success=True,
        token=token,
        name=user["name"],
        email=email,
        message="Welcome back!",
    )


@router.post("/check", response_model=AuthResponse)
def check_session(req: TokenCheckRequest):
    """Verify a session token is still valid."""
    session = _sessions.get(req.token)
    if not session:
        return AuthResponse(success=False, message="Session expired")

    return AuthResponse(
        success=True,
        token=req.token,
        name=session["name"],
        email=session["email"],
    )


@router.post("/logout")
def logout(req: TokenCheckRequest):
    """Invalidate a session token."""
    _sessions.pop(req.token, None)
    return {"success": True, "message": "Logged out"}
