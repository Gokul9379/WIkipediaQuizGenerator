from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import List

# Define output schema for quiz questions (for reference / documentation)
class QuizQuestion(BaseModel):
    question: str = Field(description="The quiz question")
    options: List[str] = Field(description="Four multiple choice options A, B, C, D")
    answer: str = Field(description="The correct answer (one of the options)")
    difficulty: str = Field(description="Difficulty level: easy, medium, or hard")
    explanation: str = Field(description="Brief explanation of why the answer is correct")
    section: str = Field(description="Which section of the article this question relates to")

class RelatedTopicsResponse(BaseModel):
    related_topics: List[str] = Field(description="List of 3-5 related Wikipedia topics")


# STRICT quiz generation template — forces concrete options and valid JSON array output
QUIZ_GENERATION_TEMPLATE = """
You are an expert quiz generator. Based only on the Article Title, Summary and Sections below,
generate exactly {num_questions} multiple-choice quiz questions.

REQUIREMENTS (must follow exactly):
- Return ONLY a valid JSON array (no markdown, no commentary).
- Each question object MUST have these fields:
  "question": string,
  "options": [4 distinct strings],
  "answer": string,                      # must be equal to one of the 4 options
  "difficulty": "easy" | "medium" | "hard",
  "explanation": string,
  "section": string

- Options must be concrete, factual answer choices (not "Option A" or "Topic A" or placeholders).
- For numeric facts, include numbers in options when relevant (e.g., years, counts).
- Distractors should be plausible and grounded in the article content.
- Cover different sections; distribute difficulty across questions.

Example (one question object only; format example):
{
  "question": "In which year was X first introduced?",
  "options": ["1910", "1920", "1930", "1940"],
  "answer": "1920",
  "difficulty": "easy",
  "explanation": "X was introduced in 1920 as mentioned in the History section.",
  "section": "History"
}

Article Title: {title}
Article Summary: {summary}
Article Sections: {sections}
Article Content (truncated): {content}

Return a JSON array of question objects exactly matching the schema above.
"""

# Related topics template — returns a JSON object with "related_topics" array
RELATED_TOPICS_TEMPLATE = """
Based on the Wikipedia article titled "{title}" with the following content:
Summary: {summary}
Sections: {sections}

Suggest 3-5 related Wikipedia topics that readers interested in this article would also find useful.

Return a JSON object with a single field "related_topics" whose value is an array of topic names, e.g.:
{{ "related_topics": ["Topic A", "Topic B", "Topic C"] }}

Return ONLY valid JSON. No markdown, no code blocks, no extra text.
"""

def get_quiz_generation_prompt(title: str, summary: str, sections: list, content: str, num_questions: int):
    """
    Create the final prompt string for quiz generation.
    - sections: a list of section headings (we join the first few)
    - content: truncated article text (we keep a safe length)
    """
    prompt = PromptTemplate(
        input_variables=["title", "summary", "sections", "content", "num_questions"],
        template=QUIZ_GENERATION_TEMPLATE
    )
    return prompt.format(
        title=title,
        summary=summary,
        sections=", ".join(sections[:5]),
        content=content[:2000],  # keep prompt length reasonable
        num_questions=num_questions
    )

def get_related_topics_prompt(title: str, summary: str, sections: list):
    """
    Create the prompt string for generating related topics.
    """
    prompt = PromptTemplate(
        input_variables=["title", "summary", "sections"],
        template=RELATED_TOPICS_TEMPLATE
    )
    return prompt.format(
        title=title,
        summary=summary,
        sections=", ".join(sections[:5])
    )
