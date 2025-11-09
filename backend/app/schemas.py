from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any, Union
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
    quiz_questions: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    related_topics: Optional[List[str]] = Field(default_factory=list)
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
    # 👇 FIXED: allow both list or dict input, so Pydantic won't break
    quiz_questions: Union[List[Dict[str, Any]], Dict[str, Any]] = Field(default_factory=list)
    related_topics: List[str] = Field(default_factory=list)
    generation_time: Optional[float] = None
    is_cached: int = 0

    class Config:
        from_attributes = True
