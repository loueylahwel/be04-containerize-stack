from pydantic import BaseModel, Field
from typing import List


class SummarizeOutput(BaseModel):
    title: str = Field(description="Short title for the text")
    bullets: List[str] = Field(description="Exactly 3 concise summary bullets", min_length=3, max_length=3)
