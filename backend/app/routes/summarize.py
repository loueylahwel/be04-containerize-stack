from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from ..ai import summarize
from ..auth import get_current_user

router = APIRouter(prefix="/api", tags=["ai"])


class SummarizeRequest(BaseModel):
    text: str


class SummarizeResponse(BaseModel):
    title: str
    bullets: list[str]


@router.post("/summarize", response_model=SummarizeResponse)
async def post_summarize(req: SummarizeRequest, current_user: dict = Depends(get_current_user)):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        result = await summarize(req.text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI provider error: {e}")

    return SummarizeResponse(title=result.title, bullets=result.bullets)
