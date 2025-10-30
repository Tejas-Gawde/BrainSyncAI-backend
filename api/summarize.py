from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional
from api.users import get_current_user
from services.summarize_service import summarize_youtube
from services.subject_service import get_subject, append_youtube_summarize_to_subject

router = APIRouter(prefix="/summarize", tags=["summarize"])


class SummarizeIn(BaseModel):
    youtube_link: HttpUrl
    subject_id: Optional[str] = None


class SummarizeOut(BaseModel):
    summary: str
    saved: Optional[bool] = None
    subject_id: Optional[str] = None


@router.post("/", response_model=SummarizeOut)
async def summarize_endpoint(payload: SummarizeIn):
    # generate summary (will raise clear errors if deps or key missing)
    try:
        summary = await summarize_youtube(str(payload.youtube_link))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to summarize: {e}")

    # if subject_id provided, validate subject exists and append
    if payload.subject_id:
        subj = await get_subject(payload.subject_id)
        if not subj:
            raise HTTPException(status_code=404, detail="Subject not found")
        # attach summary to subject
        try:
            await append_youtube_summarize_to_subject(payload.subject_id, str(payload.youtube_link), summary, added_by=current_user.get("_id"))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save summary: {e}")
        return SummarizeOut(summary=summary, saved=True, subject_id=payload.subject_id)

    return SummarizeOut(summary=summary, saved=False, subject_id=None)
