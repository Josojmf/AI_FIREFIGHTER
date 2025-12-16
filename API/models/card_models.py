"""
Card Models - Pydantic models for Memory Cards / Leitner System
===============================================================
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import re


class MemoryCardBase(BaseModel):
    question: str = Field(..., min_length=3)
    answer: str = Field(..., min_length=1)
    category: str = Field(default="General", max_length=100)
    difficulty: str = Field(default="medium", max_length=20)  # easy/medium/hard
    tags: List[str] = []


class MemoryCardCreate(MemoryCardBase):
    box: int = Field(default=1, ge=1, le=6)
    owner_id: Optional[str] = None  # usuario dueño de la tarjeta si aplica


class MemoryCardUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    tags: Optional[List[str]] = None
    box: Optional[int] = Field(default=None, ge=1, le=6)
    active: Optional[bool] = None

    class Config:
        extra = "ignore"


class MemoryCardResponse(BaseModel):
    id: str
    question: str
    answer: str
    category: str
    difficulty: str
    tags: List[str] = []
    box: int
    owner_id: Optional[str] = None
    times_reviewed: int = 0
    last_reviewed_at: Optional[datetime] = None
    created_at: datetime
    active: bool = True

    class Config:
        from_attributes = True


class MemoryCardReviewRequest(BaseModel):
    card_id: str
    result: str = Field(..., pattern="^(correct|incorrect)$")
    time_spent_seconds: Optional[int] = None


class MemoryCardReview(BaseModel):
    """
    Modelo para revisión de tarjeta de memoria (usado en historial de revisiones).
    """
    card_id: str
    result: str  # "correct" o "incorrect"
    reviewed_at: datetime
    time_spent_seconds: Optional[int] = None
    box_before: int
    box_after: int


# AÑADE ESTA CLASE FALTANTE:
class BulkMemoryCardCreate(BaseModel):
    """
    Modelo para crear múltiples tarjetas de memoria a la vez.
    """
    cards: List[MemoryCardCreate] = Field(..., min_items=1, max_items=100)
    owner_id: Optional[str] = None  # usuario dueño si aplica


class MemoryCardStats(BaseModel):
    total: int
    by_box: Dict[str, int] = {}
    by_category: Dict[str, int] = {}
    by_difficulty: Dict[str, int] = {}
    total_reviews: int
    avg_reviews_per_card: float