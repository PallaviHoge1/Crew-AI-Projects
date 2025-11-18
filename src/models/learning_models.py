from pydantic import BaseModel, HttpUrl
from typing import List, Literal, Optional

MaterialType = Literal['article', 'video', 'exercise', 'book', 'blog']

class LearningMaterial(BaseModel):
    title: str
    url: Optional[HttpUrl] = None
    source: Optional[str] = None
    type: MaterialType
    summary: Optional[str] = None
    estimated_time_minutes: Optional[int] = None
