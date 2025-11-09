# scripts/debug_quiz_generator.py
import logging
from utils.quiz_generator import QuizGenerator
from utils.scraper import WikiScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug(url):
    scraper = WikiScraper(url)
    content = scraper.get_all_content()
    title = content.get("title")
    summary = content.get("summary")
    sections = content.get("sections")
    full_content = summary + " " + " ".join(sections)

    gen = QuizGenerator()
    # Print raw call results (this method exists in the generator we ship earlier)
    raw = gen._call_model(gen.get_debug_prompt(title, summary, sections, full_content, num_questions=5))
    print("=== RAW MODEL OUTPUT ===")
    print(raw)
    try:
        cleaned = gen.clean_json_response(raw)
        print("=== CLEANED JSON ===")
        print(cleaned)
    except Exception as e:
        print("CLEAN FAILED:", e)

    # Finally run the normal generator and print repaired questions
    q = gen.generate_quiz(title, summary, sections, full_content, num_questions=5)
    print("=== FINAL QUESTIONS ===")
    import json
    print(json.dumps(q, indent=2))

if __name__ == "__main__":
    url = "https://en.wikipedia.org/wiki/Tractor"  # change as needed
    debug(url)
