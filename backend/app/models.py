from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON 
from sqlalchemy.sql import func
from datetime import datetime
from database import Base


class WikiArticle(Base):
    __tablename__ = "wiki_articles"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    raw_html = Column(Text, nullable=True)  # Cached raw HTML from Wikipedia

    # Extracted data
    key_entities = Column(JSON, nullable=True)  # {"people": [], "organizations": [], "locations": []}
    sections = Column(JSON, nullable=True)  # ["Early life", "Career", "Legacy"]

    # Generated quiz
    quiz_questions = Column(JSON, nullable=True)  # Stores quiz question set
    related_topics = Column(JSON, nullable=True)  # ["Topic1", "Topic2"]

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    generation_time = Column(Float, nullable=True)  # Time taken to generate quiz (seconds)
    is_cached = Column(Integer, default=0)  # 0 = fresh generation, 1 = cached result

    class Config:
        orm_mode = True
