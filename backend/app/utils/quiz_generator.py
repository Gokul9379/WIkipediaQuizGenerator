# app/utils/quiz_generator.py
import json
import logging
import os
import re
import random
import html
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

from langchain_google_genai import ChatGoogleGenerativeAI

from app.utils.prompt_templates import (
    get_quiz_generation_prompt,
    get_related_topics_prompt,
)

logger = logging.getLogger(__name__)
logging.getLogger("langchain_google_genai").setLevel(logging.WARNING)


class QuizGenerator:
    """
    Generate quiz questions and related topics using Google Gemini via langchain-google-genai.
    Includes robust repair, parsing, and a content-aware fallback generator.
    """

    def __init__(self, model_name: str = "models/gemini-2.5-pro", temperature: float = 0.0):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY not found in environment — model calls will fail without it.")
        # deterministic low temperature
        self.model = ChatGoogleGenerativeAI(model=model_name, temperature=temperature, api_key=api_key)

    # ----------------------
    # Low-level model call
    # ----------------------
    def _call_model(self, prompt: str) -> str:
        """
        Call the model wrapper and return text content (tries common attributes).
        """
        resp = self.model.invoke(prompt)
        # try common attributes
        text = None
        for attr in ("content", "text", "message", "result"):
            text = getattr(resp, attr, None)
            if text:
                break
        if text is None:
            text = str(resp)
        return str(text)

    # ----------------------
    # Cleaning & parsing
    # ----------------------
    @staticmethod
    def _strip_code_fences(text: str) -> str:
        text = re.sub(r"```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text, flags=re.IGNORECASE)
        return text.strip()

    @staticmethod
    def _extract_first_json(text: str) -> Optional[str]:
        text = text.strip()
        start_idx = None
        start_char = None
        for i, ch in enumerate(text):
            if ch in "[{":
                start_idx = i
                start_char = ch
                break
        if start_idx is None:
            return None
        pairs = {"[": "]", "{": "}"}
        open_ch = start_char
        close_ch = pairs[open_ch]
        depth = 0
        for j in range(start_idx, len(text)):
            if text[j] == open_ch:
                depth += 1
            elif text[j] == close_ch:
                depth -= 1
                if depth == 0:
                    return text[start_idx : j + 1]
        return None

    def clean_json_response(self, response_text: str) -> str:
        if not response_text:
            raise ValueError("Empty response from model")
        text = html.unescape(response_text)
        text = self._strip_code_fences(text)
        candidate = self._extract_first_json(text)
        if candidate:
            return candidate
        t = text.strip()
        candidate = t
        # Try replacing single quotes -> double quotes when appropriate
        if "'" in candidate and '"' not in candidate:
            candidate = candidate.replace("'", '"')
        return candidate

    # ----------------------
    # Helpers for extracting candidate distractors from content
    # ----------------------
    @staticmethod
    def _word_tokens(text: str) -> List[str]:
        # basic tokenization: words of length >=3
        return re.findall(r"\b[a-zA-Z]{3,}\b", text)

    @staticmethod
    def _extract_keyphrases(text: str, top_n: int = 10) -> List[str]:
        # simple heuristic: extract capitalized phrases and frequent words
        caps = re.findall(r"\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,}){0,2})\b", text)
        caps = list(dict.fromkeys(caps))
        words = [w.lower() for w in QuizGenerator._word_tokens(text)]
        # remove stop-ish words
        stop = set(["the", "and", "for", "with", "that", "this", "from", "which", "about", "their"])
        words = [w for w in words if w not in stop]
        freq = Counter(words)
        common = [w for w, _ in freq.most_common(15)]
        # combine: capitalized phrases first, then common words capitalized
        out = []
        for p in caps:
            if p not in out:
                out.append(p)
        for w in common:
            candidate = w.capitalize()
            if candidate not in out:
                out.append(candidate)
        return out[:top_n]

    # ----------------------
    # Option normalization and repair
    # ----------------------
    @staticmethod
    def _normalize_option_text(opt: str) -> str:
        return re.sub(r"\s+", " ", opt.strip())

    def _ensure_four_options(self, options: List[str], article_content: str) -> List[str]:
        opts = [self._normalize_option_text(o) for o in options if o and o.strip()]
        seen = set()
        cleaned = []
        for o in opts:
            if o not in seen:
                seen.add(o)
                cleaned.append(o)
        opts = cleaned
        if len(opts) >= 4:
            return opts[:4]
        # generate distractors from content
        candidates = self._extract_keyphrases(article_content, top_n=20)
        # remove any existing options
        candidates = [c for c in candidates if c not in opts]
        # if still few, add numeric placeholders or generic words
        i = 0
        while len(opts) < 4 and i < len(candidates):
            opts.append(candidates[i])
            i += 1
        fallback_words = ["History", "Function", "Usage", "Design"]
        for fw in fallback_words:
            if len(opts) >= 4:
                break
            if fw not in opts:
                opts.append(fw)
        while len(opts) < 4:
            opts.append(f"Option {len(opts)+1}")
        return opts[:4]

    def _map_answer_to_text(self, ans_raw: str, options: List[str]) -> str:
        if not ans_raw:
            return options[0]
        s = str(ans_raw).strip()
        letter_map = {"A": 0, "B": 1, "C": 2, "D": 3}
        if s.upper() in letter_map:
            idx = letter_map[s.upper()]
            if idx < len(options):
                return options[idx]
            return options[0]
        # if ans matches one option by substring
        for opt in options:
            if s.lower() in opt.lower() or opt.lower() in s.lower():
                return opt
        # fallback: prefer an exact match
        for opt in options:
            if opt.lower() == s.lower():
                return opt
        return options[0]

    def _repair_question(self, q: Dict[str, Any], article_content: str) -> Dict[str, Any]:
        repaired = {}
        repaired["question"] = str(q.get("question") or q.get("text") or q.get("prompt") or "Question").strip()
        raw_options = q.get("options") or q.get("choices") or q.get("answers") or []
        if isinstance(raw_options, dict):
            raw_options = list(raw_options.values())
        if not isinstance(raw_options, list):
            raw_options = re.split(r"\n+", str(raw_options))
        options = self._ensure_four_options(raw_options, article_content)
        answer_text = self._map_answer_to_text(q.get("answer") or q.get("correct") or "", options)
        diff = (q.get("difficulty") or "").lower()
        if diff not in ("easy", "medium", "hard"):
            diff = "easy"
        explanation = q.get("explanation") or q.get("explain") or ""
        if not explanation:
            explanation = "Based on the article content."
        section = q.get("section") or q.get("topic") or "Introduction"
        repaired["options"] = options
        repaired["answer"] = answer_text
        repaired["difficulty"] = diff
        repaired["explanation"] = explanation.strip()
        repaired["section"] = section
        return repaired

    # ----------------------
    # Strong fallback generator (content-aware)
    # ----------------------
    def _generate_fallback_quiz(self, title: str, summary: str, sections: List[str], num_questions: int = 5) -> List[Dict[str, Any]]:
        """
        Create content-grounded fallback questions.
        Uses summary + first few sections to craft:
          - main-topic question
          - numeric/year questions (if present)
          - definition/concept questions from keyphrases
          - multiple independent factual questions with plausible distractors
        """
        text = (summary or "") + " " + " ".join(sections or [])
        text = text.strip()
        keyphrases = self._extract_keyphrases(text, top_n=30)
        years = re.findall(r"\b(18|19|20)\d{2}\b", text)
        years = list(dict.fromkeys(years))

        questions: List[Dict[str, Any]] = []

        # Q1: main topic
        q1_options = [title]
        # choose other top keyphrases as distractors (cap to 3)
        distracts = [kp for kp in keyphrases if kp.lower() != title.lower()][:3]
        while len(q1_options) < 4:
            q1_options.append(distracts.pop(0) if distracts else "Other")
        questions.append({
            "question": f"What is the main subject of the article about {title}?",
            "options": q1_options,
            "answer": title,
            "difficulty": "easy",
            "explanation": f"The article title and summary indicate it is about {title}.",
            "section": "Introduction"
        })

        # numeric / year question (if years present)
        if years and len(questions) < num_questions:
            y = years[0]
            opts = [y]
            # build numeric distractors: neighboring decades
            try:
                y_int = int(y)
                distractors = [str(y_int - 10), str(y_int + 10), str(y_int + 5)]
            except:
                distractors = ["1900", "1950", "2000"]
            for d in distractors:
                if d not in opts:
                    opts.append(d)
            opts = self._ensure_four_options(opts, text)
            questions.append({
                "question": f"Which year is mentioned in the article summary about {title}?",
                "options": opts,
                "answer": y,
                "difficulty": "medium",
                "explanation": f"The summary includes the year {y}.",
                "section": "Introduction"
            })

        # Build concept questions from top keyphrases
        i = 2
        for kp in keyphrases:
            if len(questions) >= num_questions:
                break
            if kp.lower() == title.lower():
                continue
            correct = kp
            # choose other phrases as distractors
            distract = [p for p in keyphrases if p != correct][:3]
            opts = [correct] + distract
            opts = self._ensure_four_options(opts, text)
            questions.append({
                "question": f"What of the following is mentioned in the article about {title}?",
                "options": opts,
                "answer": correct,
                "difficulty": "easy",
                "explanation": f"'{correct}' appears in the article summary/sections.",
                "section": "Introduction"
            })
            i += 1

        # If still not enough, generate generic concept questions
        while len(questions) < num_questions:
            opts = self._ensure_four_options([], text)
            questions.append({
                "question": f"What is a key concept related to {title}?",
                "options": opts,
                "answer": opts[0] if opts else "Other",
                "difficulty": "easy",
                "explanation": "Fallback question generated from text heuristics.",
                "section": "Introduction"
            })

        return questions[:num_questions]

    # ----------------------
    # Public API
    # ----------------------
    def generate_quiz(
        self,
        title: str,
        summary: str,
        sections: List[str],
        content: str,
        num_questions: int = 5,
    ) -> List[Dict[str, Any]]:
        try:
            prompt = get_quiz_generation_prompt(title, summary, sections, content, num_questions)
            logger.info(f"Generating quiz for: {title}")
            raw = self._call_model(prompt)
            cleaned = self.clean_json_response(raw)
            parsed = json.loads(cleaned)
            # normalize to list
            if isinstance(parsed, dict):
                if "questions" in parsed and isinstance(parsed["questions"], list):
                    parsed_list = parsed["questions"]
                elif "quiz_questions" in parsed and isinstance(parsed["quiz_questions"], list):
                    parsed_list = parsed["quiz_questions"]
                else:
                    parsed_list = [parsed]
            elif isinstance(parsed, list):
                parsed_list = parsed
            else:
                parsed_list = [parsed]

            repaired_questions = []
            for q in parsed_list:
                if not isinstance(q, dict):
                    continue
                rq = self._repair_question(q, content)
                repaired_questions.append(rq)

            # detect placeholder output. If placeholders present -> use fallback
            def is_placeholder(qd: Dict[str, Any]) -> bool:
                opts = qd.get("options", [])
                if not opts:
                    return True
                placeholder_patterns = [r"Topic\s+[A-Z]", r"Fact\s+[A-Z]", r"Option\s+\d+", r"^A$", r"^B$", r"^C$", r"^D$"]
                counts = 0
                for o in opts:
                    for p in placeholder_patterns:
                        if re.search(p, o, flags=re.IGNORECASE):
                            counts += 1
                return counts >= 3

            if (not repaired_questions) or any(is_placeholder(qd) for qd in repaired_questions):
                logger.info("Model returned placeholders or invalid quiz — using strong fallback generation.")
                return self._generate_fallback_quiz(title, summary, sections, num_questions)

            # pad/truncate to num_questions
            if len(repaired_questions) < num_questions:
                extra = self._generate_fallback_quiz(title, summary, sections, num_questions - len(repaired_questions))
                repaired_questions.extend(extra)
            return repaired_questions[:num_questions]

        except Exception as e:
            logger.exception("Error generating quiz: %s", e)
            return self._generate_fallback_quiz(title, summary, sections, num_questions)

    def generate_related_topics(self, title: str, summary: str, sections: List[str]) -> List[str]:
        try:
            prompt = get_related_topics_prompt(title, summary, sections)
            logger.info(f"Generating related topics for: {title}")
            raw = self._call_model(prompt)
            cleaned = self.clean_json_response(raw)
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict) and "related_topics" in parsed:
                topics = parsed["related_topics"]
            elif isinstance(parsed, list):
                topics = parsed
            else:
                topics = []
            out = []
            for t in topics:
                if not isinstance(t, str):
                    continue
                s = t.strip()
                if s and s not in out:
                    out.append(s)
            return out[:5]
        except Exception as e:
            logger.exception("Error generating related topics: %s", e)
            return []
