# app/utils/prompt_templates.py
from langchain_core.prompts import PromptTemplate

QUIZ_GENERATION_TEMPLATE = """
You are an expert quiz writer. Given the Wikipedia article content below, generate exactly {num_questions}
multiple-choice questions (4 options each: A, B, C, D). Each question must be factual, grounded in the content,
and include: question, options (list of 4 full-text options), the correct answer text (not just letter), difficulty
(easy|medium|hard), short explanation, and the section name the question relates to.

Article Title: {title}
Article Summary: {summary}
Article Sections (first 5): {sections}
Article Content (truncated): {content}

Return ONLY valid JSON: a top-level array of question objects, each like:
[
  {{
    "question": "Full question text",
    "options": ["Option text A", "Option text B", "Option text C", "Option text D"],
    "answer": "Option text B",
    "difficulty": "medium",
    "explanation": "Short explanation (1-2 sentences)",
    "section": "Introduction"
  }}
]

Important:
- DO NOT return placeholders such as "Option 1", "Fact A", "Topic A" or single letters as answers.
- Options must be plausible distractors (all 4 must look like real choices).
- Provide the full option text in the "answer" field (matching exactly one of the items in options).
- Provide only JSON — no extra text, markdown, or commentary.
"""

RELATED_TOPICS_TEMPLATE = """
Given the article title "{title}", summary: {summary}, and sections: {sections},
return a JSON object with a single field "related_topics" containing a list of 3-5
related Wikipedia topic titles (as strings). Return ONLY valid JSON.

Example:
{{ "related_topics": ["Topic A", "Topic B", "Topic C"] }}
"""

def get_quiz_generation_prompt(title: str, summary: str, sections: list, content: str, num_questions: int):
    prompt = PromptTemplate(
        input_variables=["title", "summary", "sections", "content", "num_questions"],
        template=QUIZ_GENERATION_TEMPLATE
    )
    return prompt.format(
        title=title,
        summary=summary or "",
        sections=", ".join(sections[:5]) if sections else "",
        content=(content or "")[:3000],
        num_questions=num_questions,
    )

def get_related_topics_prompt(title: str, summary: str, sections: list):
    prompt = PromptTemplate(
        input_variables=["title", "summary", "sections"],
        template=RELATED_TOPICS_TEMPLATE
    )
    return prompt.format(
        title=title,
        summary=summary or "",
        sections=", ".join(sections[:5]) if sections else "",
    )
