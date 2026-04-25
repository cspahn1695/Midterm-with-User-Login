import os
import re
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from user_model import User
from schemas import UserCreate, UserLogin, TokenResponse
from auth_utils import hash_password, verify_password
from jwt_handler import create_access_token
router = APIRouter(prefix="/auth", tags=["Auth"])

# all authentication handlers are in this file. ChatGPT was used to help with some of this code, as were the in-class examples and planner project.
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



# Register (standard user only)
@router.post("/register")
async def register(user: UserCreate):
    email = _norm_email(str(user.email))
    existing = await _find_user_by_email(email)

    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = User(
        email=email,
        password=hash_password(user.password),
    )

    await new_user.insert()

    return {"message": "User created"}


# Login
@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin):
    email = _norm_email(str(user.email))
    db_user = await _find_user_by_email(email)
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/me")
async def me(email: str = Query(..., description="Logged-in user email")):
    db_user = await _find_user_by_email(email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "email": _norm_email(str(db_user.email)),
        
    }

