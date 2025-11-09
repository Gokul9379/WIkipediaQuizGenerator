from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import time
import logging
from typing import List, Dict, Any
import json

from database import get_db
from schemas import WikiArticleResponse, QuizGenerationResponse
from models import WikiArticle
from crud import QuizCRUD
from utils.scraper import WikiScraper
from utils.quiz_generator import QuizGenerator

router = APIRouter(prefix="/api/quiz", tags=["quiz"])
logger = logging.getLogger(__name__)
quiz_generator = QuizGenerator()

def _normalize_article_for_response(article) -> Dict[str, Any]:
    """
    Normalize a WikiArticle SQLAlchemy object or a dict-like into a plain dict
    suitable for Pydantic validation. Guarantees quiz_questions is always a list.
    """
    item: Dict[str, Any] = {}
    raw_quiz = None

    # Attempt attribute access (SQLAlchemy model)
    try:
        item["id"] = getattr(article, "id", None)
        item["url"] = getattr(article, "url", None)
        item["title"] = getattr(article, "title", None)
        item["summary"] = getattr(article, "summary", None) or ""
        item["key_entities"] = getattr(article, "key_entities", {}) or {}
        item["sections"] = getattr(article, "sections", []) or []
        item["related_topics"] = getattr(article, "related_topics", []) or []
        item["generation_time"] = getattr(article, "generation_time", None)
        item["is_cached"] = getattr(article, "is_cached", 0)
        raw_quiz = getattr(article, "quiz_questions", None)
    except Exception:
        # Fallback if article is a dict-like
        if isinstance(article, dict):
            item = {
                "id": article.get("id"),
                "url": article.get("url"),
                "title": article.get("title"),
                "summary": article.get("summary", "") or "",
                "key_entities": article.get("key_entities", {}) or {},
                "sections": article.get("sections", []) or [],
                "related_topics": article.get("related_topics", []) or [],
                "generation_time": article.get("generation_time", None),
                "is_cached": article.get("is_cached", 0)
            }
            raw_quiz = article.get("quiz_questions", None)
        else:
            # Last resort try to extract __dict__
            try:
                item = dict(getattr(article, "__dict__", {}) or {})
                raw_quiz = item.get("quiz_questions", None)
            except Exception:
                item = {}
                raw_quiz = None

    # If still None, check if the passed dict contains nested 'quiz_questions'
    if raw_quiz is None and isinstance(article, dict):
        if "quiz_questions" in article:
            raw_quiz = article["quiz_questions"]

    def extract_list(value):
        # If already list
        if isinstance(value, list):
            return value
        # If dict, try to find list inside common keys
        if isinstance(value, dict):
            if "questions" in value and isinstance(value["questions"], list):
                return value["questions"]
            if "quiz_questions" in value and isinstance(value["quiz_questions"], list):
                return value["quiz_questions"]
            # nested pattern
            for k in ("quiz_questions", "questions"):
                nested = value.get(k)
                if isinstance(nested, list):
                    return nested
            # If dict but not list-like, wrap it
            return [value]
        # If string, try parse JSON
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return extract_list(parsed)
            except Exception:
                return [value]
        # Other types -> wrap
        return [value]

    normalized_quiz = extract_list(raw_quiz)

    if not isinstance(normalized_quiz, list):
        normalized_quiz = [normalized_quiz]

    item["quiz_questions"] = normalized_quiz

    logger.debug(
        "Normalized article for response: id=%s quiz_questions_type=%s quiz_questions_len=%s",
        item.get("id"),
        type(item["quiz_questions"]).__name__,
        len(item["quiz_questions"]) if isinstance(item["quiz_questions"], list) else 0
    )

    return item

@router.post("/generate", response_model=QuizGenerationResponse)
async def generate_quiz(url: str, db: Session = Depends(get_db)):
    try:
        existing = QuizCRUD.get_article_by_url(db, url)
        if existing and existing.quiz_questions:
            normalized = _normalize_article_for_response(existing)
            return QuizGenerationResponse.model_validate(normalized)

        scraper = WikiScraper(url)
        if not scraper.validate_url():
            raise HTTPException(status_code=400, detail="Invalid Wikipedia URL")

        start_time = time.time()
        content = scraper.get_all_content()

        full_content = content.get("summary", "") + " " + " ".join(content.get("sections", []) or [])

        quiz_questions = quiz_generator.generate_quiz(
            content.get("title", ""),
            content.get("summary", ""),
            content.get("sections", []) or [],
            full_content
        )

        related_topics = quiz_generator.generate_related_topics(
            content.get("title", ""),
            content.get("summary", ""),
            content.get("sections", []) or []
        )

        generation_time = time.time() - start_time

        article_data = {
            "url": url,
            "title": content.get("title", ""),
            "summary": content.get("summary", ""),
            "raw_html": content.get("raw_html"),
            "key_entities": content.get("key_entities"),
            "sections": content.get("sections"),
            "quiz_questions": quiz_questions,
            "related_topics": related_topics,
            "generation_time": generation_time,
            "is_cached": 0
        }

        if existing:
            article = QuizCRUD.update_article(db, existing.id, article_data)
        else:
            article = QuizCRUD.create_article(db, article_data)

        normalized = _normalize_article_for_response(article)
        return QuizGenerationResponse.model_validate(normalized)

    except HTTPException:
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Article URL already exists")
    except Exception as e:
        logger.error(f"Error generating quiz: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=List[QuizGenerationResponse])
async def get_history(skip: int = Query(0), limit: int = Query(10), db: Session = Depends(get_db)):
    try:
        articles = QuizCRUD.get_all_articles(db, skip=skip, limit=limit)
        return [QuizGenerationResponse.model_validate(_normalize_article_for_response(a)) for a in articles]
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{article_id}", response_model=QuizGenerationResponse)
async def get_quiz_details(article_id: int, db: Session = Depends(get_db)):
    try:
        article = QuizCRUD.get_article_by_id(db, article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Quiz not found")
        normalized = _normalize_article_for_response(article)
        return QuizGenerationResponse.model_validate(normalized)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quiz: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/history/{article_id}")
async def delete_quiz(article_id: int, db: Session = Depends(get_db)):
    try:
        success = QuizCRUD.delete_article(db, article_id)
        if not success:
            raise HTTPException(status_code=404, detail="Quiz not found")
        return {"message": "Quiz deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting quiz: {e}")
        raise HTTPException(status_code=500, detail=str(e))
