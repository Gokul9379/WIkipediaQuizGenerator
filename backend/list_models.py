# list_models.py (fixed)
import os
from dotenv import load_dotenv
load_dotenv()

from google import genai

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise SystemExit("Set GOOGLE_API_KEY in .env before running list_models.py")

client = genai.Client(api_key=api_key)

print("Available models:")
pager = client.models.list()   # returns an iterable/pager
for model in pager:
    # model may be a resource object; print name and a repr just in case
    name = getattr(model, "name", None) or str(model)
    print("-", name)
