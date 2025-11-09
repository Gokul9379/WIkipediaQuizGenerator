# scripts/normalize_quiz_questions.py
import os, sys, json
from sqlalchemy.orm import Session
from database import SessionLocal
from models import WikiArticle

def normalize_quiz_questions():
    db: Session = SessionLocal()
    try:
        articles = db.query(WikiArticle).all()
        changed = 0
        for a in articles:
            qq = a.quiz_questions
            original = qq
            normalized = None

            # If None -> set empty list
            if qq is None:
                normalized = []
            # If dict and contains "quiz_questions" key that is a list -> unwrap
            elif isinstance(qq, dict):
                # common wrapper shapes:
                # 1) {"quiz_questions": [...]}
                # 2) {"questions": [...]} or {"quiz": [...]}
                for k in ("quiz_questions", "questions", "quiz"):
                    if k in qq and isinstance(qq[k], list):
                        normalized = qq[k]
                        break
                # if dict but already is the question object (single question), wrap into list
                if normalized is None:
                    # If dict looks like a single question (has "question" key), wrap it
                    if "question" in qq:
                        normalized = [qq]
                    else:
                        # unknown dict shape -> try to find any list inside values
                        for val in qq.values():
                            if isinstance(val, list):
                                normalized = val
                                break

            elif isinstance(qq, list):
                normalized = qq

            # fallback: convert strings that look like JSON
            if normalized is None and isinstance(qq, str):
                try:
                    parsed = json.loads(qq)
                    if isinstance(parsed, list):
                        normalized = parsed
                except Exception:
                    normalized = None

            # Final fallback: if still None -> set empty list
            if normalized is None:
                normalized = []

            # If changed, assign and commit
            if normalized != original:
                a.quiz_questions = normalized
                db.add(a)
                changed += 1

        if changed > 0:
            db.commit()
        print(f"Normalization complete. Articles checked: {len(articles)}. Modified: {changed}")
    finally:
        db.close()

if __name__ == "__main__":
    normalize_quiz_questions()
