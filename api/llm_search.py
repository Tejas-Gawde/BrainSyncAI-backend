from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from api.users import get_current_user
from services.llm_search_service import run_search
from services.subject_service import get_subject, append_llm_search_to_subject

router = APIRouter(prefix="/llm-search", tags=["llm-search"])


class LLMSearchIn(BaseModel):
    query: str
    subject_id: Optional[str] = None


class LLMSearchOut(BaseModel):
    result: str
    saved: Optional[bool] = None
    subject_id: Optional[str] = None


@router.post("/", response_model=LLMSearchOut)
async def llm_search_endpoint(payload: LLMSearchIn):
    try:
        result = run_search(payload.query)
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    if payload.subject_id:
        subj = await get_subject(payload.subject_id)
        if not subj:
            raise HTTPException(status_code=404, detail="Subject not found")
        try:
            await append_llm_search_to_subject(payload.subject_id, payload.query, result, added_by=current_user.get("_id"))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save conversation: {e}")
        return LLMSearchOut(result=result, saved=True, subject_id=payload.subject_id)

    return LLMSearchOut(result=result, saved=False, subject_id=None)
