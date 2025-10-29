from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional
from api.users import get_current_user
from services.pdf_chat_service import chat_with_pdf
from services.subject_service import get_subject, append_pdf_chat_to_subject

router = APIRouter(prefix="/chat-pdf", tags=["chat-pdf"])


@router.post("/")
async def chat_pdf_endpoint(
    pdf_file: UploadFile = File(...),
    message: str = Form(...),
    subject_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
):
    # read file bytes
    file_bytes = await pdf_file.read()

    # run the PDF chat
    try:
        answer = await chat_with_pdf(file_bytes, message)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {e}")

    # optionally save conversation under subject
    if subject_id:
        subj = await get_subject(subject_id)
        if not subj:
            raise HTTPException(status_code=404, detail="Subject not found")
        try:
            await append_pdf_chat_to_subject(subject_id, message, answer, pdf_filename=pdf_file.filename, added_by=current_user.get("_id"))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save conversation: {e}")

    return {"answer": answer, "saved": bool(subject_id)}
