import os
import re
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from user_model import User
from schemas import UserCreate, UserLogin, TokenResponse
from auth_utils import hash_password, verify_password
from jwt_handler import create_access_token
router = APIRouter(prefix="/auth", tags=["Auth"])


def _norm_email(value: str) -> str:
    return (value or "").strip().lower()


async def _find_user_by_email(value: str):
    """Match stored user; handles legacy DB rows that may not be lowercased."""
    e = _norm_email(value)
    if not e:
        return None
    user = await User.find_one(User.email == e)
    if user:
        return user
    return await User.find_one(
        {"email": {"$regex": f"^{re.escape(value.strip())}$", "$options": "i"}}
    )


def _bootstrap_secret() -> str:
    return os.getenv("ADMIN_BOOTSTRAP_SECRET", "dev-bootstrap-change-me")


# ✅ Register (standard user only)
@router.post("/register")
async def register(user: UserCreate):
    email = _norm_email(str(user.email))
    existing = await _find_user_by_email(email)

    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = User(
        email=email,
        password=hash_password(user.password),
        is_admin=False,
    )

    await new_user.insert()

    return {"message": "User created"}


# ✅ Login
@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin):
    email = _norm_email(str(user.email))
    db_user = await _find_user_by_email(email)
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    is_admin = getattr(db_user, "is_admin", False)
    token, expire = create_access_token(
        {"email": email, "role": "admin" if is_admin else "user"}
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=int((expire - datetime.now(timezone.utc)).total_seconds()),
        email=email,
        is_admin=bool(is_admin),
    )


@router.get("/me")
async def me(email: str = Query(..., description="Logged-in user email")):
    db_user = await _find_user_by_email(email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "email": _norm_email(str(db_user.email)),
        
    }

