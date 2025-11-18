from pydantic import BaseModel
from typing import List, Literal, Optional

Difficulty = Literal['easy', 'medium', 'hard']

class MCQ(BaseModel):
    question: str
    options: List[str]
    answer_index: int
    explanation: Optional[str] = None
    difficulty: Difficulty = 'medium'

class Quiz(BaseModel):
    topic: str
    questions: List[MCQ]
