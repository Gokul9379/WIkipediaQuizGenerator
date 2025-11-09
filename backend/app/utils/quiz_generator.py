# app/utils/quiz_generator.py
import json
import logging
import os
import re
import random
import html
from typing import List, Dict, Any, Optional

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
    - Picks a working model by default (change model_name when needed)
    - Cleans LLM responses and validates/repairs output
    """

    def __init__(self, model_name: str = "models/gemini-2.5-pro", temperature: float = 0.0):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY not found in environment — model calls will fail without it.")
        # Use deterministic low temperature for factual outputs
        self.model = ChatGoogleGenerativeAI(model=model_name, temperature=temperature, api_key=api_key)

    # ----------------------
    # Low-level model call
    # ----------------------
    def _call_model(self, prompt: str) -> str:
        """
        Call the model wrapper and return text content (tries common attributes).
        """
        resp = self.model.invoke(prompt)
        # The response object shape differs between wrapper versions; try common fields
        text = None
        for attr in ("content", "text", "message", "result"):
            text = getattr(resp, attr, None)
            if text:
                break
        if text is None:
            # Fallback to str(resp)
            text = str(resp)
        # ensure string
        return str(text)

    # ----------------------
    # Cleaning & parsing
    # ----------------------
    @staticmethod
    def _strip_code_fences(text: str) -> str:
        # remove triple-backtick code blocks and language markers
        text = re.sub(r"```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text, flags=re.IGNORECASE)
        return text.strip()

    @staticmethod
    def _extract_first_json(text: str) -> Optional[str]:
        """
        Find the substring that starts with the first '[' or '{' and ends with the matching bracket.
        This is conservative: finds the outermost JSON (array or object).
        """
        text = text.strip()
        # find first bracket
        start_idx = None
        start_char = None
        for i, ch in enumerate(text):
            if ch in "[{":
                start_idx = i
                start_char = ch
                break
        if start_idx is None:
            return None

        # find matching closing bracket using a simple counter
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
        """
        Clean the model response and return a JSON string (or raise ValueError).
        """
        if not response_text:
            raise ValueError("Empty response from model")

        text = html.unescape(response_text)  # unescape HTML entities
        text = self._strip_code_fences(text)

        candidate = self._extract_first_json(text)
        if candidate:
            return candidate

        # Last-resort heuristics: try to fix common issues (single quotes -> double quotes)
        t = text.strip()
        # Try to find a substring between the first newline separated JSON-like block
        # fallback to the whole text
        candidate = t
        # Try a simple replacement fix (only if it seems like JSON with single quotes)
        if "'" in candidate and '"' not in candidate:
            candidate = candidate.replace("'", '"')

        return candidate

    # ----------------------
    # Repair & validation
    # ----------------------
    @staticmethod
    def _normalize_option_text(opt: str) -> str:
        return opt.strip()

    def _ensure_four_options(self, options: List[str], article_content: str) -> List[str]:
        """
        Ensure exactly 4 options. If less, create plausible distractors from article_content.
        If more, trim to 4.
        """
        opts = [self._normalize_option_text(o) for o in options if o and o.strip()]
        # dedupe preserving order
        seen = set()
        cleaned = []
        for o in opts:
            if o not in seen:
                seen.add(o)
                cleaned.append(o)
        opts = cleaned

        # if we have >=4, cut to 4
        if len(opts) >= 4:
            return opts[:4]

        # build distractors: try to extract capitalized phrases or nouns from article_content
        distractors = []
        # 1) years/numbers not in correct options
        numbers = re.findall(r"\b(19|20)\d{2}\b", article_content)
        numbers = list(dict.fromkeys(numbers))
        for n in numbers:
            if n not in opts:
                distractors.append(n)

        # 2) Capitalized phrase extraction (simple heuristic)
        caps = re.findall(r"\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,}){0,2})\b", article_content)
        for c in caps:
            if c not in opts and c not in distractors:
                distractors.append(c)

        # 3) fallback generic distractors (short)
        fallback_words = ["History", "Agriculture", "Technology", "Economy", "Mechanics", "Function"]
        for fw in fallback_words:
            if fw not in opts and fw not in distractors:
                distractors.append(fw)

        # add distractors until we have 4
        i = 0
        while len(opts) < 4 and i < len(distractors):
            opts.append(distractors[i])
            i += 1

        # if still short, append simple variants
        while len(opts) < 4:
            opts.append(f"Option {len(opts)+1}")

        return opts[:4]

    def _repair_question(self, q: Dict[str, Any], article_content: str) -> Dict[str, Any]:
        """
        Normalize & repair a single question object.
        Expected keys: question, options (list), answer, difficulty, explanation, section
        """
        repaired = {}

        repaired["question"] = str(q.get("question") or q.get("text") or "Question").strip()
        raw_options = q.get("options") or q.get("choices") or q.get("answers") or []
        if isinstance(raw_options, dict):
            # sometimes models return labelled dicts {"A": "x", "B": "y"}
            raw_options = list(raw_options.values())
        if not isinstance(raw_options, list):
            # attempt to split by newline
            raw_options = re.split(r"\n+", str(raw_options))

        options = self._ensure_four_options(raw_options, article_content)

        # answer: try to get full text answer; allow 'A'/'B' letters
        ans = q.get("answer") or q.get("correct") or ""
        ans_str = str(ans).strip()
        # if answer is single-letter like 'A', map to option
        letter_map = {"A": 0, "B": 1, "C": 2, "D": 3}
        if ans_str.upper() in letter_map:
            idx = letter_map[ans_str.upper()]
            if idx < len(options):
                answer_text = options[idx]
            else:
                answer_text = options[0]
        else:
            # try to find closest match among options
            match = None
            for opt in options:
                if ans_str and ans_str.lower() in opt.lower():
                    match = opt
                    break
            answer_text = match or options[0]

        # difficulty normalization
        diff = (q.get("difficulty") or "").lower()
        if diff not in ("easy", "medium", "hard"):
            diff = "easy"

        explanation = q.get("explanation") or q.get("explain") or ""
        if not explanation:
            explanation = "Based on the article content."

        section = q.get("section") or "Introduction"

        repaired["options"] = options
        repaired["answer"] = answer_text
        repaired["difficulty"] = diff
        repaired["explanation"] = explanation.strip()
        repaired["section"] = section

        return repaired

    # ----------------------
    # Fallback question generator (fact-oriented)
    # ----------------------
    def _generate_fallback_quiz(self, title: str, summary: str, num_questions: int = 5) -> List[Dict[str, Any]]:
        """
        Create simple factual / concept questions using the summary text:
        - Q1: main topic
        - Other Qs: ask about numbers/years or extract important noun phrases
        This fallback is deterministic and grounded in article text.
        """
        summary_text = (summary or "").strip()
        questions: List[Dict[str, Any]] = []

        # Helper: extract candidate phrases
        caps = re.findall(r"\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,}){0,2})\b", summary_text)
        caps = list(dict.fromkeys(caps))  # unique
        years = re.findall(r"\b(18|19|20)\d{2}\b", summary_text)
        years = list(dict.fromkeys(years))

        # Q1: main topic
        main_q = {
            "question": f"What is the main topic of this article about {title}?",
            "options": [title, (caps[0] if caps else "History"), (caps[1] if len(caps) > 1 else "Technology"), "Other"],
            "answer": title,
            "difficulty": "easy",
            "explanation": f"The article is about {title}.",
            "section": "Introduction",
        }
        questions.append(main_q)

        # Additional questions: try to generate up to num_questions total
        seeds = []

        # numeric question if we have years
        if years:
            seeds.append(("Which year is mentioned in the article summary?", years))

        # use capitalized phrases as facts
        if caps:
            seeds.append(("Which of these is mentioned in the article summary?", caps))

        # generic conceptual fallback
        seeds.append(("Which term relates to the article topic?", ["Agriculture", "Technology", "Economy", "Culture"]))

        # build from seeds
        for i, (qtext, pool) in enumerate(seeds, start=2):
            if len(questions) >= num_questions:
                break
            pool_list = list(dict.fromkeys(pool))
            correct = pool_list[0] if pool_list else "Fact A"
            # build options: correct + random others
            opts = [str(correct)]
            other_choices = [p for p in pool_list[1:]] + ["Fact B", "Fact C", "Fact D", "Other"]
            random.shuffle(other_choices)
            while len(opts) < 4:
                opts.append(str(other_choices.pop(0)))
            qobj = {
                "question": f"{i}. {qtext}",
                "options": opts,
                "answer": str(correct),
                "difficulty": "easy",
                "explanation": f"Derived from article summary: {correct}",
                "section": "Introduction",
            }
            questions.append(qobj)

        # If still fewer than required, clone simple concept questions
        while len(questions) < num_questions:
            idx = len(questions) + 1
            qobj = {
                "question": f"What is a key concept related to {title}? (fallback {idx})",
                "options": ["Fact A", "Fact B", "Fact C", "Fact D"],
                "answer": "Fact A",
                "difficulty": "easy",
                "explanation": "Fallback question generated from summary heuristics.",
                "section": "Introduction",
            }
            questions.append(qobj)

        return questions[:num_questions]

    # ----------------------
    # Public API: generate_quiz & generate_related_topics
    # ----------------------
    def generate_quiz(
        self,
        title: str,
        summary: str,
        sections: List[str],
        content: str,
        num_questions: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Generate quiz questions using the model; returns list of question dicts:
        {
            "question": str,
            "options": [str, str, str, str],
            "answer": str,
            "difficulty": "easy"/"medium"/"hard",
            "explanation": str,
            "section": str
        }
        """
        try:
            prompt = get_quiz_generation_prompt(title, summary, sections, content, num_questions)
            logger.info(f"Generating quiz for: {title}")
            raw = self._call_model(prompt)
            cleaned = self.clean_json_response(raw)

            parsed = json.loads(cleaned)

            # reduce to list of question dicts
            if isinstance(parsed, dict):
                # check common keys
                if "questions" in parsed and isinstance(parsed["questions"], list):
                    parsed_list = parsed["questions"]
                elif isinstance(parsed.get("quiz_questions"), list):
                    parsed_list = parsed["quiz_questions"]
                else:
                    # maybe the LLM returned a single question object
                    parsed_list = [parsed]
            elif isinstance(parsed, list):
                parsed_list = parsed
            else:
                parsed_list = [parsed]

            # normalize and repair every question
            repaired_questions = []
            for q in parsed_list:
                if not isinstance(q, dict):
                    # skip invalid entries
                    continue
                rq = self._repair_question(q, content)
                repaired_questions.append(rq)

            # If result seems like placeholders (Topic A etc) or too few, fallback
            # detect placeholder by checking options content length
            def is_placeholder(qd: Dict[str, Any]) -> bool:
                opts = qd.get("options", [])
                if not opts:
                    return True
                placeholder_patterns = [r"Topic\s+[A-Z]", r"Fact\s+[A-Z]", r"Option\s+\d+"]
                counts = 0
                for o in opts:
                    for p in placeholder_patterns:
                        if re.search(p, o, flags=re.IGNORECASE):
                            counts += 1
                # if most options look like placeholders -> return True
                return counts >= 3

            if not repaired_questions or any(is_placeholder(qd) for qd in repaired_questions):
                logger.info("Model returned placeholders or invalid quiz — using fallback generation.")
                return self._generate_fallback_quiz(title, summary, num_questions)

            # ensure we return exactly num_questions (truncate/pad with fallback)
            if len(repaired_questions) < num_questions:
                extra = self._generate_fallback_quiz(title, summary, num_questions - len(repaired_questions))
                repaired_questions.extend(extra)
            return repaired_questions[:num_questions]

        except Exception as e:
            logger.exception("Error generating quiz: %s", e)
            # fallback
            return self._generate_fallback_quiz(title, summary, num_questions)

    def generate_related_topics(self, title: str, summary: str, sections: List[str]) -> List[str]:
        """
        Generate related topics list (3-5 items)
        """
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
            # sanitize -> strings only, strip, unique
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

