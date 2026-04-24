# used ChatGPT to help write this code; added comments where appropriate.
import os
import re
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from ai_matcher import (
    analyze_skill_gap,
    compute_match_score,
    extract_job_text,
    extract_resume_text,
)
from application_model import Application
from authenticate import authenticate
from jwt_handler import TokenData
from schemas import ApplicationCreate, JobTextRequest
from user_model import User

router = APIRouter(prefix="/applications", tags=["Applications"])
UPLOAD_FOLDER = "uploads"


def _app_owner_filter(current_user: User) -> dict:
    return {"Owner.$id": current_user.id}


async def _get_current_user(token_data: TokenData = Depends(authenticate)) -> User:
    current_user = await User.find_one(User.email == token_data.email)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists"
        )
    return current_user


async def _get_owned_application(app_id: str, current_user: User) -> Application:
    try:
        oid = ObjectId(app_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    app = await Application.find_one({"_id": oid, **_app_owner_filter(current_user)})
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.post("/")
async def create_application(
    app: ApplicationCreate, current_user: User = Depends(_get_current_user)
):
    new_app = Application(
        Owner=current_user, **app.dict()
    )  # bind application ownership to logged-in user
    await new_app.insert()
    return new_app


@router.post("/{app_id}/resume")
async def upload_resume(
    app_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(_get_current_user),
):
    application = await _get_owned_application(app_id, current_user)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    file_path = f"{UPLOAD_FOLDER}/{app_id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    application.resume_path = file_path
    await application.save()
    return {"message": "Resume uploaded", "file_path": file_path}


@router.get("/")
async def get_applications(
    status: Optional[List[str]] = Query(None),
    company: Optional[str] = Query(None),
    current_user: User = Depends(_get_current_user),
):
    query_filters = _app_owner_filter(current_user)

    if status:
        query_filters["status"] = {"$in": status}

    if company:
        query_filters["company"] = {"$regex": f".*{re.escape(company)}.*", "$options": "i"}

    return await Application.find(query_filters).to_list()


@router.get("/{app_id}")
async def get_application(app_id: str, current_user: User = Depends(_get_current_user)):
    return await _get_owned_application(app_id, current_user)


@router.put("/{app_id}")
async def update_application(
    app_id: str,
    updated_app: ApplicationCreate,
    current_user: User = Depends(_get_current_user),
):
    app = await _get_owned_application(app_id, current_user)
    await app.set(updated_app.dict())
    return app


@router.delete("/{app_id}")
async def delete_application(app_id: str, current_user: User = Depends(_get_current_user)):
    app = await _get_owned_application(app_id, current_user)
    await app.delete()
    return {"message": "deleted"}


@router.get("/{app_id}/match")
async def get_match_score(app_id: str, current_user: User = Depends(_get_current_user)):
    application = await _get_owned_application(app_id, current_user)

    if not application.resume_path:
        raise HTTPException(status_code=400, detail="No resume uploaded")

    if not application.jobpostinglink:
        raise HTTPException(status_code=400, detail="No job posting link")

    resume_text = extract_resume_text(application.resume_path)
    job_text = extract_job_text(application.jobpostinglink)
    if len((job_text or "").strip()) < 80:
        raise HTTPException(
            status_code=400,
            detail="Could not extract enough text from that job link (extracted < 80 chars). The URL may block scrapers. Try a public posting URL or include the LinkedIn job URL that contains the numeric job ID.",
        )
    score = compute_match_score(resume_text, job_text)
    matched_skills, missing_skills = analyze_skill_gap(resume_text, job_text)

    return {
        "match_score": score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
    }


@router.post("/{app_id}/match")
async def get_match_score_from_text(
    app_id: str,
    body: JobTextRequest,
    current_user: User = Depends(_get_current_user),
):
    application = await _get_owned_application(app_id, current_user)

    if not application.resume_path:
        raise HTTPException(status_code=400, detail="No resume uploaded")

    if len((body.job_text or "").strip()) < 80:
        raise HTTPException(
            status_code=400,
            detail="Pasted job description is too short. Please paste more of the posting text.",
        )

    resume_text = extract_resume_text(application.resume_path)
    score = compute_match_score(resume_text, body.job_text)
    matched_skills, missing_skills = analyze_skill_gap(resume_text, body.job_text)

    return {
        "match_score": score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
    }


