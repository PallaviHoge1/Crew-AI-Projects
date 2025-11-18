from pydantic import BaseModel
from typing import List, Literal, Optional

Difficulty = Literal['beginner', 'intermediate', 'advanced']

class ProjectIdea(BaseModel):
    title: str
    description: str
    difficulty: Difficulty
    estimated_hours: Optional[int] = None
    steps: Optional[List[str]] = None
    required_skills: Optional[List[str]] = None
