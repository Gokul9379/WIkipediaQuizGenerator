from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class QuestionSchema(BaseModel):
    question: str
    options: List[str] = Field(default_factory=list)
    answer: str
    difficulty: str  # "easy", "medium", "hard"
    explanation: str

class WikiArticleCreate(BaseModel):
    url: HttpUrl

class WikiArticleResponse(BaseModel):
    id: int
    url: str
    title: str
    summary: Optional[str] = None
    key_entities: Optional[Dict[str, List[str]]] = None
    sections: Optional[List[str]] = None
    quiz_questions: Optional[List[Dict[str, Any]]] = None
    related_topics: Optional[List[str]] = None
    created_at: datetime
    generation_time: Optional[float] = None
    is_cached: int = 0

    class Config:
        from_attributes = True

class QuizGenerationResponse(BaseModel):
    id: int
    url: str
    title: str
    summary: str
    key_entities: Dict[str, List[str]]
    sections: List[str]
    quiz_questions: List[Dict[str, Any]]
    related_topics: List[str]
    generation_time: Optional[float] = None
    is_cached: int = 0

    class Config:
        from_attributes = True
