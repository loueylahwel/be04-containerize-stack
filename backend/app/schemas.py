from typing import Optional
from pydantic import BaseModel


class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ItemOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
