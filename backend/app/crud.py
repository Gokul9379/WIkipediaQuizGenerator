from sqlalchemy.orm import Session
from models import WikiArticle
from schemas import WikiArticleCreate
from typing import Optional, List

class QuizCRUD:
    @staticmethod
    def create_article(db: Session, article_data: dict) -> WikiArticle:
        """Create new wiki article record"""
        db_article = WikiArticle(**article_data)
        db.add(db_article)
        db.commit()
        db.refresh(db_article)
        return db_article

    @staticmethod
    def get_article_by_url(db: Session, url: str) -> Optional[WikiArticle]:
        """Get article by URL"""
        return db.query(WikiArticle).filter(WikiArticle.url == url).first()

    @staticmethod
    def get_article_by_id(db: Session, article_id: int) -> Optional[WikiArticle]:
        """Get article by ID"""
        return db.query(WikiArticle).filter(WikiArticle.id == article_id).first()

    @staticmethod
    def get_all_articles(db: Session, skip: int = 0, limit: int = 100) -> List[WikiArticle]:
        """Get all articles with pagination"""
        return db.query(WikiArticle).offset(skip).limit(limit).all()

    @staticmethod
    def update_article(db: Session, article_id: int, update_data: dict) -> Optional[WikiArticle]:
        """Update article"""
        article = db.query(WikiArticle).filter(WikiArticle.id == article_id).first()
        if article:
            for key, value in update_data.items():
                setattr(article, key, value)
            db.commit()
            db.refresh(article)
        return article

    @staticmethod
    def delete_article(db: Session, article_id: int) -> bool:
        """Delete article"""
        article = db.query(WikiArticle).filter(WikiArticle.id == article_id).first()
        if article:
            db.delete(article)
            db.commit()
            return True
        return False
